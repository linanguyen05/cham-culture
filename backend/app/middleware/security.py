"""Lightweight CSRF defense for same-origin cookie sessions.

Unsafe requests must originate from the same host as the server, an explicitly
allowed origin, or (when configured) omit the Origin/Referer header entirely.
"""

from urllib.parse import urlparse

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import Settings


class OriginGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            candidate = request.headers.get("origin") or request.headers.get("referer")
            if not candidate:
                if self.settings.allow_missing_origin_for_unsafe_methods:
                    return await call_next(request)
                return self._forbidden()
            if self._allowed(candidate, request):
                return await call_next(request)
            return self._forbidden()
        return await call_next(request)

    def _allowed(self, candidate: str, request: Request) -> bool:
        parsed = urlparse(candidate)
        # Same-origin: the request comes from the page this backend served.
        if parsed.netloc == request.url.netloc:
            return True
        normalized = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
        return normalized in self.settings.frontend_origins

    @staticmethod
    def _forbidden() -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"error": "FORBIDDEN", "message": "Nguồn yêu cầu không hợp lệ."},
        )
