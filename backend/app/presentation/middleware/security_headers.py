from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Defense-in-depth response headers. No CSP here — the SPA is a Vite bundle
    and a wrong CSP would silently break it; add one deliberately if this is ever
    served on a public domain, tuned to the actual script/style sources in use."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response
