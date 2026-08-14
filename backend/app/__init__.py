"""Cham Culture — unified backend application factory.

One professional FastAPI service that:
  * serves the canonical frontend SPA and uploaded media (same origin),
  * exposes the clean Community/Profile API (``/api/community/*``),
  * exposes session-based auth (``/api/auth/*``) plus compatibility routes
    (``/login``, ``/register``, ``/update_profile``) for the existing frontend,
all backed by local SQLite + local filesystem storage (no cloud dependency).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.auth.routes import router as auth_router
from app.community.routes import router as community_router
from app.config import get_settings
from app.extensions import lifespan_context
from app.middleware.security import OriginGuardMiddleware
from app.profile.routes import router as profile_router
from app.rate_limit import limiter
from app.web import mount_static


def _validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "Dữ liệu không hợp lệ"
    first = errors[0]
    location = ".".join(str(item) for item in first.get("loc", []) if item != "body")
    message = first.get("msg", "Dữ liệu không hợp lệ")
    return f"{location}: {message}" if location else message


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with lifespan_context(settings) as resources:
            app.state.resources = resources
            yield

    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.state.limiter = limiter

    async def rate_limit_handler(_, __):
        return JSONResponse(
            status_code=429,
            content={"error": "RATE_LIMITED", "message": "Bạn thao tác quá nhanh. Vui lòng thử lại sau."},
        )

    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_middleware(OriginGuardMiddleware, settings=settings)

    if settings.frontend_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.frontend_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Accept", "Origin"],
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {
            "error": "HTTP_ERROR",
            "message": str(exc.detail),
        }
        return JSONResponse(status_code=exc.status_code, content=detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": "VALIDATION_ERROR", "message": _validation_message(exc)},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_, exc: Exception):
        import logging

        logging.getLogger(__name__).exception("Unhandled application error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_SERVER_ERROR", "message": "Đã xảy ra lỗi máy chủ."},
        )

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(community_router)
    app.include_router(profile_router)

    # Static mounts must come last so /api/* and compat routes win.
    mount_static(app, settings)
    return app
