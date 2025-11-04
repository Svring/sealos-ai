from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

app = FastAPI()


import json


import os

load_dotenv()


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")

        # Skip x-secret check if origin is from smith.langchain.com
        if origin != "https://smith.langchain.com":
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
