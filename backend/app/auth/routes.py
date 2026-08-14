"""Authentication endpoints.

Two families of routes share one session mechanism:

* ``/api/auth/*`` — clean JSON API consumed by community.js.
* ``/login``, ``/register``, ``/update_profile`` — compatibility routes that
  match the exact request/response shapes the existing (unmodifiable) frontend
  SPA (frontend/index.html, frontend/profile.js) already expects.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, EmailStr, Field

from app.auth.service import UserService, verify_password
from app.config import Settings, get_settings
from app.middleware.auth import (
    CurrentUser,
    build_session_payload,
    clear_session_cookie,
    get_current_user,
    set_session_cookie,
)
from app.rate_limit import limiter

router = APIRouter(tags=["Authentication"])


# --------------------------------------------------------------------------- #
# Clean API (community.js)
# --------------------------------------------------------------------------- #
api = APIRouter(prefix="/api/auth")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


def _service(request: Request) -> UserService:
    return UserService(request.app.state.resources.db)


def _public_user(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "username": row.get("username") or "Người dùng",
        "email": row.get("email") or "",
        "avatar_url": row.get("avatar_url"),
    }


@api.get("/me")
async def me(user: CurrentUser = Depends(get_current_user)) -> dict[str, Any]:
    return {
        "authenticated": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar_url": user.avatar_url,
        },
    }


@api.post("/login")
@limiter.limit(get_settings().rate_limit_login)
async def api_login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    svc = _service(request)
    user = await svc.get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail={"error": "AUTHENTICATION_REQUIRED", "message": "Email hoặc mật khẩu không đúng."},
        )
    set_session_cookie(response, settings, build_session_payload(user["id"], user["email"]))
    return {"authenticated": True, "user": _public_user(user)}


@api.post("/logout")
async def api_logout(response: Response, settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    clear_session_cookie(response, settings)
    return {"authenticated": False}


router.include_router(api)


# --------------------------------------------------------------------------- #
# Compatibility routes for the existing frontend SPA
# --------------------------------------------------------------------------- #
class CredsRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


@router.post("/register")
@limiter.limit(get_settings().rate_limit_login)
async def compat_register(
    payload: CredsRequest,
    request: Request,
) -> dict[str, Any]:
    """frontend/index.html handleRegister: expects ok + {message, userId}."""
    if len(payload.password) < 8:
        raise HTTPException(422, detail={"message": "Mật khẩu phải có ít nhất 8 ký tự."})
    svc = _service(request)
    if await svc.get_by_email(payload.email) is not None:
        raise HTTPException(409, detail={"message": "Email đã được đăng ký. Vui lòng đăng nhập."})
    user = await svc.create(email=payload.email, password=payload.password)
    return {"message": "Đăng ký thành công. Hãy hoàn tất hồ sơ.", "userId": user["id"]}


@router.post("/login")
@limiter.limit(get_settings().rate_limit_login)
async def compat_login(
    payload: CredsRequest,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """frontend/index.html handleLogin: 404 unknown email, 401 bad password,
    else ok + {message, user:{user_id, username, avatar_url}} + session cookie."""
    svc = _service(request)
    user = await svc.get_by_email(payload.email)
    if user is None:
        raise HTTPException(404, detail={"message": "Email chưa được đăng ký."})
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(401, detail={"message": "Sai mật khẩu."})
    set_session_cookie(response, settings, build_session_payload(user["id"], user["email"]))
    return {
        "message": "Đăng nhập thành công.",
        "user": {
            "user_id": user["id"],
            "username": user.get("username") or "Người dùng",
            "avatar_url": user.get("avatar_url"),
        },
    }


@router.post("/update_profile")
async def compat_update_profile(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
    username: str = Form(...),
    userId: str = Form(default=""),
    avatar: UploadFile | None = File(default=None),
) -> dict[str, Any]:
    """frontend/profile.js: multipart {username, avatar?, userId}. The user has
    just registered (no session yet), so the id arrives in the ``userId`` field.
    On success we set the session cookie and return the updated user."""
    resources = request.app.state.resources
    svc = _service(request)

    resolved_id = (userId or "").strip()
    if not resolved_id:
        token = request.cookies.get(settings.session_cookie_name)
        if token:
            try:
                from app.middleware.auth import _decode_session

                resolved_id = str(_decode_session(settings, token).get("user_id", "")).strip()
            except ValueError:
                resolved_id = ""
    if not resolved_id:
        raise HTTPException(400, detail={"error": "BAD_REQUEST", "message": "Thiếu userId."})

    user = await svc.get_by_id(resolved_id)
    if user is None:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "Người dùng không tồn tại."})

    clean_username = username.strip()
    if not clean_username:
        raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": "Tên người dùng không được để trống."})

    avatar_url: str | None = None
    if avatar is not None and avatar.filename:
        data = await avatar.read()
        if data:
            if len(data) > settings.max_image_size_bytes:
                raise HTTPException(422, detail={"error": "VALIDATION_ERROR", "message": "Ảnh vượt quá dung lượng cho phép."})
            avatar_url = await resources.storage.save_avatar(
                data, avatar.content_type or "", avatar.filename
            )

    updated = await svc.update_profile(
        user_id=resolved_id, username=clean_username, avatar_url=avatar_url
    )
    assert updated is not None

    set_session_cookie(response, settings, build_session_payload(updated["id"], updated["email"]))
    return {
        "message": "Lưu thông tin thành công.",
        "user": {
            "user_id": updated["id"],
            "username": updated.get("username") or "Người dùng",
            "avatar_url": updated.get("avatar_url"),
        },
    }
