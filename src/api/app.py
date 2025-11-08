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
        # Log request method and path (optional)
        # print(f"Request: {request.method} {request.url.path}")
        # print(f"Origin: {request.headers.get('origin')}")
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
