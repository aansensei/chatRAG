import os
import re
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

# Job-status polling is a cheap, read-only cache lookup (no LLM/embedding cost) and is
# legitimately called at high frequency when uploading many files at once — e.g.
# syncing a folder with dozens of files, each polled every couple seconds until done.
# Counting it against the same budget as expensive endpoints turns ordinary bulk
# uploads into a wave of false "upload failed" errors once the budget is exhausted.
_JOB_STATUS_RE = re.compile(r"^/ingest/jobs/[^/]+$")


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Only the API routes that trigger real cost (LLM calls, OCR/embedding jobs) —
        # static assets (/assets/*, /) are excluded so loading the page itself can't
        # exhaust the budget and lock a legitimate user out.
        if not path.startswith(_LIMITED_PREFIXES):
            return await call_next(request)
        if request.method == "GET" and _JOB_STATUS_RE.match(path):
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
