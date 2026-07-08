from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
from uuid import uuid4
import time

app = FastAPI()

# These are frontend origins allowed to call this API from browser
origins = [
    "https://app-ag28dm.example.com"
]
EMAIL = "23ds1000074@ds.study.iitm.ac.in"  # replace with your real logged-in email

# 1) Request-context middleware
class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

# 2) Per-client rate limiting middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit=11, window_seconds=10):
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self.clients = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_id = request.headers.get("X-Client-Id", "anonymous")
        now = time.time()
        bucket = self.clients[client_id]

        while bucket and now - bucket[0] > self.window_seconds:
            bucket.popleft()

        if len(bucket) >= self.limit:
            return Response(content='{"detail":"Too Many Requests"}', status_code=429, media_type="application/json")

        bucket.append(now)
        return await call_next(request)

# Add middleware in a safe order
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    #allow_origins=origins,          # Do not use ["*"] for real apps with login/cookies
    allow_origins=["*"],
    #allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_methods=["*"],
    #allow_headers=["Authorization", "Content-Type"],
    allow_headers=["*"]
)

app.add_middleware(RateLimitMiddleware, limit=11, window_seconds=10)

@app.get("/ping")
async def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id
    }
