import asyncio
import json
import logging
import os
from typing import Any, Awaitable, Callable

import requests

from src.lib.quota.free_tier import QuotaUnavailableError, refund_free_turn
from src.lib.quota.identity import resolve_entitlement_key
from src.lib.quota.quota_logging import (
    ensure_quota_logging_configured,
    log_quota_event,
    log_request_context,
    log_request_status,
    mask_secret,
    new_request_id,
)
from src.lib.quota.resolve_credentials import (
    BillingCredentials,
    acquire_billing_credentials,
    resolve_platform_openai_credentials,
)

ensure_quota_logging_configured()

Send = Callable[[dict[str, Any]], Awaitable[None]]
Receive = Callable[[], Awaitable[dict[str, Any]]]


def _graph_input(payload: dict[str, Any]) -> dict[str, Any]:
    raw_input = payload.get("input")
    if isinstance(raw_input, dict):
        return raw_input
    return {}


def _extract_session_id(
    payload: dict[str, Any], graph_input: dict[str, Any]
) -> str | None:
    metadata = payload.get("metadata") if isinstance(payload, dict) else None
    candidates = [
        graph_input.get("session_id"),
        graph_input.get("sessionId"),
        metadata.get("sessionId") if isinstance(metadata, dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def _apply_credentials(
    graph_input: dict[str, Any], credentials: BillingCredentials
) -> None:
    graph_input["base_url"] = credentials.base_url
    graph_input["api_key"] = credentials.api_key
    if credentials.billing == "free":
        graph_input["trial"] = True


def _quota_headers(credentials: BillingCredentials) -> dict[str, str]:
    return {
        "X-Chat-Billing": credentials.billing,
        "X-Chat-Free-Remaining": str(credentials.snapshot.remaining),
        "X-Chat-Free-Limit": str(credentials.snapshot.limit),
    }


def _deny_payload(reason: str) -> tuple[int, dict[str, Any]]:
    if reason == "exhausted":
        return (
            402,
            {
                "error": "Free chat quota exhausted. Configure billing credentials to continue.",
                "code": "FREE_QUOTA_EXHAUSTED",
            },
        )
    if reason == "subscription_ineligible":
        return (
            403,
            {
                "error": (
                    "Free chat quota is only available for an active Sealos Free "
                    "subscription (plan_name=Free with a valid expire_at)."
                ),
                "code": "FREE_QUOTA_SUBSCRIPTION_INELIGIBLE",
            },
        )
    if reason == "no_platform_creds":
        return (
            503,
            {
                "error": "Platform AI credentials are not configured and no user credentials were provided.",
                "code": "FREE_QUOTA_UNCONFIGURED",
            },
        )
    return (
        503,
        {"error": "Free chat quota unavailable.", "code": "FREE_QUOTA_UNAVAILABLE"},
    )


def _chunk_indicates_error(chunk: bytes) -> bool:
    try:
        text = chunk.decode("utf-8", errors="ignore")
    except Exception:
        return False
    lowered = text.lower()
    return "event: error" in lowered or "event:error" in lowered


def _header_value(scope: dict[str, Any], name: str) -> str | None:
    target = name.lower().encode()
    for key, value in scope.get("headers", []):
        if key.lower() == target:
            return value.decode("latin-1")
    return None


async def _read_request_body(receive: Receive) -> bytes:
    chunks: list[bytes] = []
    while True:
        message = await receive()
        if message["type"] == "http.request":
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        elif message["type"] == "http.disconnect":
            break
    return b"".join(chunks)


async def _send_json(send: Send, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body, "more_body": False})


async def _authenticate_kubeconfig(
    kubeconfig_encoded: str,
) -> tuple[int, dict[str, Any]] | None:
    frontend_url = os.getenv("SEALOS_BRAIN_FRONTEND_URL", "").strip()
    if not frontend_url:
        return 500, {"error": "SEALOS_BRAIN_FRONTEND_URL not configured"}

    auth_url = f"{frontend_url.rstrip('/')}/api/auth"
    headers = {
        "authorization": kubeconfig_encoded,
        "Content-Type": "application/json",
    }

    loop = asyncio.get_running_loop()
    try:
        auth_response = await loop.run_in_executor(
            None,
            lambda: requests.post(
                auth_url, headers=headers, verify=False, timeout=10.0
            ),
        )
    except requests.RequestException as exc:
        return 503, {"error": f"Authentication service error: {exc}"}

    if auth_response.status_code != 200:
        message = "Unauthorized"
        try:
            message = auth_response.json().get("error", message)
        except Exception:
            pass
        return 401, {"error": message}

    return None


class FreeQuotaStreamMiddleware:
    """Pure ASGI middleware — reliably rewrites the run/stream request body.

    ``BaseHTTPMiddleware`` does not propagate a replaced request body to the
    inner app; LangGraph was still reading the client's original ``base_url`` /
    ``api_key`` from thread checkpoint state / the untouched POST body.
    """

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope: dict[str, Any], receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "")
        path = scope.get("path", "")
        if method != "POST" or not path.endswith("/runs/stream"):
            await self.app(scope, receive, send)
            return

        ensure_quota_logging_configured()
        request_id = new_request_id()
        loop = asyncio.get_running_loop()

        kubeconfig_encoded = _header_value(scope, "authorization")
        if not kubeconfig_encoded:
            log_quota_event(
                "request_rejected",
                request_id=request_id,
                reason="missing_authorization",
            )
            await _send_json(send, 401, {"error": "Unauthorized"})
            return

        auth_error = await _authenticate_kubeconfig(kubeconfig_encoded)
        if auth_error is not None:
            status, payload = auth_error
            log_quota_event(
                "request_rejected",
                request_id=request_id,
                reason="kubeconfig_auth_failed",
                status_code=status,
            )
            await _send_json(send, status, payload)
            return

        body = await _read_request_body(receive)
        if not body:
            log_quota_event(
                "request_rejected", request_id=request_id, reason="missing_body"
            )
            await _send_json(send, 400, {"error": "Missing run payload"})
            return

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            log_quota_event(
                "request_rejected", request_id=request_id, reason="invalid_json"
            )
            await _send_json(send, 400, {"error": "Invalid JSON body"})
            return

        if not isinstance(payload, dict):
            log_quota_event(
                "request_rejected",
                request_id=request_id,
                reason="invalid_payload_shape",
            )
            await _send_json(send, 400, {"error": "Invalid run payload"})
            return

        graph_input = _graph_input(payload)
        session_id = _extract_session_id(payload, graph_input)
        trial = bool(graph_input.get("trial"))
        entitlement_key = resolve_entitlement_key(
            kubeconfig_encoded=kubeconfig_encoded,
            trial=trial,
            session_id=session_id,
        )
        if not entitlement_key:
            log_quota_event(
                "request_rejected",
                request_id=request_id,
                reason="entitlement_key_unresolved",
                trial=trial,
                session_id=session_id,
            )
            await _send_json(
                send,
                400,
                {"error": "Could not resolve quota identity from kubeconfig"},
            )
            return

        client_base_url = graph_input.get("base_url")
        client_api_key = graph_input.get("api_key")

        log_request_context(
            request_id=request_id,
            path=path,
            entitlement_key=entitlement_key,
            session_id=session_id,
            trial=trial,
            plan_name=graph_input.get("plan_name"),
            expire_at=graph_input.get("expire_at"),
            model_name=graph_input.get("model_name"),
            user_base_url=client_base_url,
            user_api_key=client_api_key,
            platform_configured=resolve_platform_openai_credentials() is not None,
        )

        try:
            credentials, reason = await loop.run_in_executor(
                None,
                lambda: acquire_billing_credentials(
                    entitlement_key=entitlement_key,
                    user_base_url=client_base_url,
                    user_api_key=client_api_key,
                    model_name=graph_input.get("model_name"),
                    plan_name=graph_input.get("plan_name"),
                    expire_at=graph_input.get("expire_at"),
                    request_id=request_id,
                ),
            )
        except QuotaUnavailableError as exc:
            log_request_status(
                request_id=request_id,
                phase="rejected",
                entitlement_key=entitlement_key,
                outcome="error",
                reason="quota_unavailable",
                detail=str(exc),
            )
            await _send_json(
                send,
                503,
                {
                    "error": "Free chat quota service unavailable.",
                    "code": "FREE_QUOTA_UNAVAILABLE",
                    "detail": str(exc),
                },
            )
            return

        if credentials is None:
            log_request_status(
                request_id=request_id,
                phase="denied",
                entitlement_key=entitlement_key,
                outcome="denied",
                deny_reason=reason,
                client_base_url=client_base_url,
                client_api_key=mask_secret(client_api_key),
                plan_name=graph_input.get("plan_name"),
                expire_at=graph_input.get("expire_at"),
            )
            status, deny_payload = _deny_payload(reason)
            await _send_json(send, status, deny_payload)
            return

        _apply_credentials(graph_input, credentials)
        payload["input"] = graph_input
        modified_body = json.dumps(payload).encode("utf-8")
        quota_headers = _quota_headers(credentials)

        log_quota_event(
            "downstream_body_prepared",
            request_id=request_id,
            entitlement_key=entitlement_key,
            billing=credentials.billing,
            original_body_size=len(body),
            modified_body_size=len(modified_body),
            input_keys=sorted(graph_input.keys()),
            sent_base_url=graph_input.get("base_url"),
            sent_api_key=mask_secret(graph_input.get("api_key")),
            sent_trial=graph_input.get("trial"),
            sent_model_name=graph_input.get("model_name"),
        )

        log_request_status(
            request_id=request_id,
            phase="allowed",
            entitlement_key=entitlement_key,
            outcome="allowed",
            billing=credentials.billing,
            quota={
                "limit": credentials.snapshot.limit,
                "used": credentials.snapshot.used,
                "remaining": credentials.snapshot.remaining,
            },
            client_base_url=client_base_url,
            client_api_key=mask_secret(client_api_key),
            injected_base_url=credentials.base_url,
            injected_api_key=mask_secret(credentials.api_key),
            plan_name=graph_input.get("plan_name"),
            expire_at=graph_input.get("expire_at"),
            response_headers=quota_headers,
        )

        body_sent = False

        async def receive_with_modified_body() -> dict[str, Any]:
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {
                    "type": "http.request",
                    "body": modified_body,
                    "more_body": False,
                }
            # Body already delivered. SSE/inner middleware poll receive() to
            # listen for disconnects; we must NOT emit another http.request
            # (Starlette's BaseHTTPMiddleware raises if it sees two of those).
            # Forward to the original receive so http.disconnect propagates.
            return await receive()

        track_free = credentials.billing == "free"
        status_code = 200
        saw_error = False
        stream_completed = False
        refunded = False

        async def maybe_refund(phase: str, **extra: Any) -> None:
            nonlocal refunded
            if not track_free or refunded:
                return
            refunded = True
            log_request_status(
                request_id=request_id,
                phase=phase,
                entitlement_key=entitlement_key,
                outcome="refund",
                billing="free",
                **extra,
            )
            await loop.run_in_executor(None, refund_free_turn, entitlement_key)

        async def send_with_quota(message: dict[str, Any]) -> None:
            nonlocal status_code, saw_error, stream_completed

            if message["type"] == "http.response.start":
                status_code = message.get("status", 200)
                headers = list(message.get("headers", []))
                for key, value in quota_headers.items():
                    headers.append((key.encode("latin-1"), value.encode("latin-1")))
                message = {**message, "headers": headers}

                if track_free:
                    if status_code == 200:
                        log_request_status(
                            request_id=request_id,
                            phase="stream_started",
                            entitlement_key=entitlement_key,
                            outcome="streaming",
                            billing="free",
                            status_code=status_code,
                        )
                    else:
                        await maybe_refund(
                            "stream_non_200", status_code=status_code
                        )

            elif message["type"] == "http.response.body":
                chunk = message.get("body", b"")
                if (
                    track_free
                    and chunk
                    and not saw_error
                    and _chunk_indicates_error(chunk)
                ):
                    saw_error = True
                if not message.get("more_body", False):
                    stream_completed = True
                    if track_free and status_code == 200 and not refunded:
                        if saw_error:
                            await maybe_refund(
                                "stream_incomplete",
                                saw_error=True,
                            )
                        else:
                            log_request_status(
                                request_id=request_id,
                                phase="finished",
                                entitlement_key=entitlement_key,
                                outcome="success",
                                billing="free",
                            )

            await send(message)

        try:
            await self.app(scope, receive_with_modified_body, send_with_quota)
        except Exception as exc:
            if track_free:
                await maybe_refund("stream_error", detail=str(exc))
            raise
        finally:
            if (
                track_free
                and status_code == 200
                and not stream_completed
                and not refunded
            ):
                await maybe_refund("stream_aborted", completed=False)
