import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Checked against Content-Length before Starlette parses the multipart body, so an
# oversized upload is rejected without ever being spooled to disk. Browser
# multipart/form-data uploads always send Content-Length, so this covers the
# real-world case; a request that omits it (unusual for a file upload) falls
# through uncapped.
_MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_MB", "50")) * 1024 * 1024
_UPLOAD_PATHS = ("/ingest/upload", "/ingest/documents/")  # covers /upload and /{id}/relink


class MaxUploadSizeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and any(request.url.path.startswith(p) for p in _UPLOAD_PATHS):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > _MAX_UPLOAD_BYTES:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"File quá lớn. Giới hạn {_MAX_UPLOAD_BYTES // (1024 * 1024)}MB."},
                )
        return await call_next(request)
