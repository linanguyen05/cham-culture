from typing import Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, EmailStr, Field

from app.auth.service import AuthService
from app.config import Settings, get_settings
from app.middleware.auth import CurrentUser, clear_session_cookie, get_current_user, set_session_cookie
from app.rate_limit import limiter

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


@router.get("/me")
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


@router.post("/login")
@limiter.limit(get_settings().rate_limit_login)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    resources = request.app.state.resources
    auth = AuthService(resources, settings)
    auth_payload = await auth.sign_in(payload.email, payload.password)
    auth_user = auth_payload.get("user") or {}
    user_id = str(auth_user.get("id", ""))

    async with resources.db_pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT id::text, username, email, avatar_url
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            row = await cur.fetchone()

    if row is None:
        from fastapi import HTTPException
        raise HTTPException(403, detail={"error": "FORBIDDEN", "message": "Tài khoản Auth chưa có bản ghi tương ứng trong users."})

    user_row = {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "avatar_url": row[3],
    }
    set_session_cookie(response, settings, auth.build_session_payload(auth_payload, user_row))
    return {
        "authenticated": True,
        "user": user_row,
    }


@router.post("/logout")
async def logout(response: Response, settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    clear_session_cookie(response, settings)
    return {"authenticated": False}
