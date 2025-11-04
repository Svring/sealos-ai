from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

app = FastAPI()


import json


import os

load_dotenv()


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        # Log request method and path
        # print(f"Request: {request.method} {request.url.path}")
        # print(f"X-Secret: {request.headers.get('x-secret')}")
        # print(f"Origin: {origin}")

        # Build whitelist: substrings allowed to bypass secret check
        whitelist_substrings = [
            "localhost:3000",
            "usw.sealos.io",
            "192.168.12.53.nip.io",
        ]
        allowed_origin = os.getenv("SEALOS_BRAIN_FRONTEND_URL")
        # Consider explicit full-origin allows as well
        explicit_allowed = [
            "https://smith.langchain.com",
            allowed_origin,
        ]

        origin_allowed = False
        if origin:
            # Substring match against whitelist
            origin_allowed = any(s in origin for s in whitelist_substrings)
            # Exact match against explicit allowed origins (ignoring Nones)
            if not origin_allowed:
                origin_allowed = any(
                    ea for ea in explicit_allowed if ea and origin == ea
                )

        # Enforce secret check only when not allowed by origin and not /info path
        if not origin_allowed and request.url.path != "/info":
            langgraph_secret = os.getenv("LANGGRAPH_SECRET")
            x_secret = request.headers.get("x-secret")
            if langgraph_secret is not None and x_secret != langgraph_secret:
                from starlette.responses import JSONResponse

                return JSONResponse(
                    status_code=401, content={"detail": "Invalid X-Secret header"}
                )

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
