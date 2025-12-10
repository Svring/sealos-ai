from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
import asyncio
import os

load_dotenv()

app = FastAPI()


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
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
        response.headers["X-Custom-Header"] = "Hello from middleware!"
        return response


# Add the middleware to the app
app.add_middleware(CustomHeaderMiddleware)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
