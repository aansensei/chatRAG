import os
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# In-memory per-IP sliding window — fine for a single-process local/internal
# deployment. Would need a shared store (e.g. Redis, already used elsewhere in
# this app for the job queue) if this ever runs as multiple instances behind a
# load balancer, since each process would otherwise track its own counts.
_WINDOW_SECONDS = 60
_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30"))
_history: dict[str, deque[float]] = defaultdict(deque)


_LIMITED_PREFIXES = ("/chat", "/ingest", "/memory")


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only the API routes that trigger real cost (LLM calls, OCR/embedding jobs) —
        # static assets (/assets/*, /) are excluded so loading the page itself can't
        # exhaust the budget and lock a legitimate user out.
        if not request.url.path.startswith(_LIMITED_PREFIXES):
            return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = _history[client_ip]
        while bucket and now - bucket[0] > _WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= _MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": f"Quá nhiều request. Giới hạn {_MAX_REQUESTS}/phút, thử lại sau."},
            )
        bucket.append(now)
        return await call_next(request)
