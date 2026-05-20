from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
import asyncio
import os
import re
import json

from src.api.free_quota_middleware import FreeQuotaStreamMiddleware

load_dotenv()

app = FastAPI()

# UUID pattern for route matching
UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def thread_path(suffix: str = "") -> re.Pattern:
    """Generate regex pattern for thread paths with optional suffix."""
    return re.compile(f"^/threads/{UUID}{suffix}$", re.IGNORECASE)


# Define allowed routes
ALLOWED_ROUTES = [
    {"method": "POST", "pattern": re.compile("^/threads$", re.IGNORECASE)},
    {"method": "POST", "pattern": re.compile("^/threads/search$", re.IGNORECASE)},
    {"method": "GET", "pattern": thread_path()},
    {"method": "GET", "pattern": thread_path("/state")},
    {"method": "POST", "pattern": thread_path("/state")},
    {"method": "GET", "pattern": thread_path("/history")},
    {"method": "DELETE", "pattern": thread_path()},
    {"method": "PATCH", "pattern": thread_path()},
    {"method": "POST", "pattern": thread_path("/runs/stream")},
    {
        "method": "POST",
        "pattern": re.compile(f"^/threads/{UUID}/runs/{UUID}/cancel$", re.IGNORECASE),
    },
    {"method": "POST", "pattern": re.compile("^/title$", re.IGNORECASE)},
    {"method": "POST", "pattern": re.compile("^/repo/scan$", re.IGNORECASE)},
    {"method": "POST", "pattern": re.compile("^/repo/ship$", re.IGNORECASE)},
]


class RouteValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate that requests match allowed routes."""

    async def dispatch(self, request: Request, call_next):
        method = request.method
        path = request.url.path

        # Check if the request matches any allowed route
        is_allowed = any(
            route["method"] == method and route["pattern"].match(path)
            for route in ALLOWED_ROUTES
        )

        if not is_allowed:
            return JSONResponse({"error": "Endpoint not allowed"}, status_code=403)

        # If route is allowed, continue with the request
        response = await call_next(request)
        return response


class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip validation for streaming endpoints
        if "/runs/stream" in request.url.path:
            response = await call_next(request)
            return response

        # Get authorization header (encoded kubeconfig)
        kubeconfig_encoded = request.headers.get("authorization")

        if not kubeconfig_encoded:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        # Get SEALOS_BRAIN_FRONTEND_URL from environment
        frontend_url = os.getenv("SEALOS_BRAIN_FRONTEND_URL")
        if not frontend_url:
            return JSONResponse(
                {"error": "SEALOS_BRAIN_FRONTEND_URL not configured"}, status_code=500
            )

        # Make POST request to auth endpoint
        auth_url = f"{frontend_url}/api/auth"
        headers = {
            "authorization": kubeconfig_encoded,
            "Content-Type": "application/json",
        }

        try:
            # Run requests.post in a thread pool to avoid blocking
            loop = asyncio.get_running_loop()
            auth_response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    auth_url, headers=headers, verify=False, timeout=10.0
                ),
            )

            if auth_response.status_code != 200:
                error_message = "Unauthorized"
                try:
                    error_data = auth_response.json()
                    error_message = error_data.get("error", error_message)
                except:
                    pass
                return JSONResponse({"error": error_message}, status_code=401)

            # Parse auth response to get owner
            auth_data = auth_response.json()
            owner = auth_data.get("owner")

            # Store kubeconfig_encoded in request state for filtering
            request.state.kubeconfig_encoded = kubeconfig_encoded
        except requests.RequestException as e:
            return JSONResponse(
                {"error": f"Authentication service error: {str(e)}"}, status_code=503
            )
        except Exception as e:
            return JSONResponse(
                {"error": f"Authentication failed: {str(e)}"}, status_code=401
            )

        # If auth succeeds, continue with the request
        response = await call_next(request)
        if owner:
            response.headers["owner"] = owner
        return response


class ThreadSearchFilterMiddleware(BaseHTTPMiddleware):
    """Middleware to filter threads/search results based on kubeconfig."""

    async def dispatch(self, request: Request, call_next):
        # Only filter /threads/search POST requests
        if request.method == "POST" and request.url.path.lower() == "/threads/search":
            # Get kubeconfig_encoded directly from authorization header
            kubeconfig_encoded = request.headers.get("authorization")

            # Continue with the request
            response = await call_next(request)

            # Only filter if we have kubeconfig_encoded and response is successful
            if kubeconfig_encoded and response.status_code == 200:
                try:
                    # Read response body with timeout protection
                    response_body = b""

                    # Read from iterator with timeout to prevent hanging
                    async def read_body():
                        nonlocal response_body
                        async for chunk in response.body_iterator:
                            response_body += chunk
                            # Safety check: limit max body size to prevent memory issues (10MB)
                            if len(response_body) > 10 * 1024 * 1024:
                                raise ValueError("Response body too large")

                    # Read with timeout to prevent hanging (10 seconds should be enough)
                    await asyncio.wait_for(read_body(), timeout=10.0)

                    # Parse JSON response
                    if not response_body:
                        return response

                    data = json.loads(response_body.decode("utf-8"))

                    # Filter threads based on values.kubeconfig
                    if isinstance(data, dict) and "data" in data:
                        # If response has a "data" field containing threads
                        threads = data.get("data", [])
                        if isinstance(threads, list):
                            filtered_threads = [
                                thread
                                for thread in threads
                                if self._should_include_thread(
                                    thread, kubeconfig_encoded
                                )
                            ]
                            data["data"] = filtered_threads
                    elif isinstance(data, list):
                        # If response is directly a list of threads
                        data = [
                            thread
                            for thread in data
                            if self._should_include_thread(thread, kubeconfig_encoded)
                        ]

                    # Create new response with filtered data
                    filtered_response = JSONResponse(data, status_code=200)
                    # Copy headers from original response
                    for key, value in response.headers.items():
                        if key.lower() not in ["content-length", "content-type"]:
                            filtered_response.headers[key] = value
                    return filtered_response
                except asyncio.TimeoutError:
                    # If reading times out, return original response
                    return response
                except (json.JSONDecodeError, Exception):
                    # If response is not JSON or parsing fails, return original response
                    return response

            return response

        # For non-search requests, continue normally
        response = await call_next(request)
        return response

    def _should_include_thread(self, thread: dict, kubeconfig_encoded: str) -> bool:
        """Check if thread should be included in response.

        Only include threads where values.kubeconfig matches the authorization header.
        Exclude threads where kubeconfig is missing or different from authorization header.
        """
        if not isinstance(thread, dict):
            return False

        # Get values.kubeconfig
        values = thread.get("values", {})
        if not isinstance(values, dict):
            return False

        thread_kubeconfig = values.get("kubeconfig")

        # Only include if kubeconfig is present and matches the authorization header
        if thread_kubeconfig is not None and thread_kubeconfig == kubeconfig_encoded:
            return True

        return False


# Add middleware to the app (order matters - route validation first)
app.add_middleware(RouteValidationMiddleware)
app.add_middleware(FreeQuotaStreamMiddleware)
app.add_middleware(AuthorizationMiddleware)
app.add_middleware(ThreadSearchFilterMiddleware)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
