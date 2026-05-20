import asyncio
import json
import os
from typing import Any

import requests
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.lib.quota.free_tier import QuotaUnavailableError, refund_free_turn
from src.lib.quota.identity import resolve_entitlement_key
from src.lib.quota.resolve_credentials import (
    BillingCredentials,
    acquire_billing_credentials,
)


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


def _deny_response(reason: str) -> JSONResponse:
    if reason == "exhausted":
        return JSONResponse(
            {
                "error": "Free chat quota exhausted. Configure billing credentials to continue.",
                "code": "FREE_QUOTA_EXHAUSTED",
            },
            status_code=402,
        )
    if reason == "no_platform_creds":
        return JSONResponse(
            {
                "error": "Platform AI credentials are not configured and no user credentials were provided.",
                "code": "FREE_QUOTA_UNCONFIGURED",
            },
            status_code=503,
        )
    return JSONResponse(
        {"error": "Free chat quota unavailable.", "code": "FREE_QUOTA_UNAVAILABLE"},
        status_code=503,
    )


def _chunk_indicates_error(chunk: bytes) -> bool:
    """Heuristically detect a LangGraph SSE ``event: error`` frame."""
    try:
        text = chunk.decode("utf-8", errors="ignore")
    except Exception:
        return False
    lowered = text.lower()
    return "event: error" in lowered or "event:error" in lowered


async def _authenticate_kubeconfig(kubeconfig_encoded: str) -> JSONResponse | None:
    """Verify the kubeconfig against brain's ``/api/auth``.

    Returns ``None`` on success, or a ``JSONResponse`` to short-circuit the
    request with the appropriate status code on failure.
    """
    frontend_url = os.getenv("SEALOS_BRAIN_FRONTEND_URL", "").strip()
    if not frontend_url:
        return JSONResponse(
            {"error": "SEALOS_BRAIN_FRONTEND_URL not configured"},
            status_code=500,
        )

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
        return JSONResponse(
            {"error": f"Authentication service error: {exc}"},
            status_code=503,
        )

    if auth_response.status_code != 200:
        message = "Unauthorized"
        try:
            message = auth_response.json().get("error", message)
        except Exception:
            pass
        return JSONResponse({"error": message}, status_code=401)

    return None


class FreeQuotaStreamMiddleware(BaseHTTPMiddleware):
    """Authenticate the kubeconfig and enforce per-namespace free turns on
    LangGraph streaming runs (``POST .../runs/stream``).

    Important guarantees:

    - The quota key is derived from the kubeconfig only AFTER the kubeconfig
      has been verified by brain. A forged kubeconfig cannot consume someone
      else's quota.
    - When the entitlements DB is unreachable or unconfigured, the middleware
      fails CLOSED (503) instead of letting requests through as unlimited.
    - A free turn is reserved BEFORE the upstream stream starts and is
      refunded if the stream fails to start, returns a non-200, errors mid
      stream, or the client disconnects.
    """

    async def dispatch(self, request: Request, call_next):
        if request.method != "POST" or not request.url.path.endswith("/runs/stream"):
            return await call_next(request)

        kubeconfig_encoded = request.headers.get("authorization")
        if not kubeconfig_encoded:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        auth_error = await _authenticate_kubeconfig(kubeconfig_encoded)
        if auth_error is not None:
            return auth_error

        body = await request.body()
        if not body:
            return JSONResponse({"error": "Missing run payload"}, status_code=400)

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

        if not isinstance(payload, dict):
            return JSONResponse({"error": "Invalid run payload"}, status_code=400)

        graph_input = _graph_input(payload)
        session_id = _extract_session_id(payload, graph_input)
        entitlement_key = resolve_entitlement_key(
            kubeconfig_encoded=kubeconfig_encoded,
            trial=bool(graph_input.get("trial")),
            session_id=session_id,
        )
        if not entitlement_key:
            return JSONResponse(
                {"error": "Could not resolve quota identity from kubeconfig"},
                status_code=400,
            )

        loop = asyncio.get_running_loop()
        try:
            credentials, reason = await loop.run_in_executor(
                None,
                lambda: acquire_billing_credentials(
                    entitlement_key=entitlement_key,
                    user_base_url=graph_input.get("base_url"),
                    user_api_key=graph_input.get("api_key"),
                    model_name=graph_input.get("model_name"),
                ),
            )
        except QuotaUnavailableError as exc:
            return JSONResponse(
                {
                    "error": "Free chat quota service unavailable.",
                    "code": "FREE_QUOTA_UNAVAILABLE",
                    "detail": str(exc),
                },
                status_code=503,
            )

        if credentials is None:
            return _deny_response(reason)

        _apply_credentials(graph_input, credentials)
        payload["input"] = graph_input
        modified_body = json.dumps(payload).encode("utf-8")
        quota_headers = _quota_headers(credentials)

        async def receive():
            return {
                "type": "http.request",
                "body": modified_body,
                "more_body": False,
            }

        downstream_request = Request(request.scope, receive)
        # Some Starlette internals look at ``_body`` directly.
        downstream_request._body = modified_body

        try:
            response = await call_next(downstream_request)
        except Exception:
            if credentials.billing == "free":
                await loop.run_in_executor(
                    None, refund_free_turn, entitlement_key
                )
            raise

        for key, value in quota_headers.items():
            response.headers[key] = value

        if credentials.billing != "free":
            return response

        if response.status_code != 200:
            await loop.run_in_executor(None, refund_free_turn, entitlement_key)
            return response

        return self._wrap_stream_for_refund(response, entitlement_key)

    def _wrap_stream_for_refund(
        self, response: Response, entitlement_key: str
    ) -> Response:
        """Wrap a streaming response so that the previously reserved free turn
        is refunded when the stream errors out, emits a LangGraph
        ``event: error`` frame, or the client disconnects mid-stream.
        """
        if not hasattr(response, "body_iterator"):
            return response

        original_iterator = response.body_iterator

        async def stream_with_refund():
            saw_error = False
            completed = False
            try:
                async for chunk in original_iterator:
                    if not saw_error and _chunk_indicates_error(chunk):
                        saw_error = True
                    yield chunk
                completed = True
            finally:
                if not completed or saw_error:
                    try:
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(
                            None, refund_free_turn, entitlement_key
                        )
                    except Exception:
                        pass

        return StreamingResponse(
            stream_with_refund(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
