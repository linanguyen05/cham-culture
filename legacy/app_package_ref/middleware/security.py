from urllib.parse import urlparse

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import Settings


class OriginGuardMiddleware(BaseHTTPMiddleware):
    """Lightweight CSRF defense for same-origin cookie sessions.

    Unsafe requests must either come from an allowed Origin/Referer host or omit
    the header only when explicitly allowed by configuration (useful for tests
    and non-browser service calls)."""

    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")
            candidate = origin or referer
            if not candidate and self.settings.allow_missing_origin_for_unsafe_methods:
                return await call_next(request)

            if candidate and self._allowed(candidate):
                return await call_next(request)

            return JSONResponse(
                status_code=403,
                content={
                    "error": "FORBIDDEN",
                    "message": "Nguồn yêu cầu không hợp lệ.",
                },
            )
        return await call_next(request)

    def _allowed(self, candidate: str) -> bool:
        parsed = urlparse(candidate)
        normalized = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        return normalized in self.settings.frontend_origins
