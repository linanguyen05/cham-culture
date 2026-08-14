import base64
import json
import time
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, Request, Response

from app.config import Settings, get_settings
from app.extensions import AppResources


@dataclass(frozen=True)
class CurrentUser:
    id: str
    username: str
    email: str
    avatar_url: str | None


def _fernet(settings: Settings) -> Fernet:
    # Derive a stable 32-byte Fernet key from SECRET_KEY without exposing it.
    import hashlib

    digest = hashlib.sha256(settings.secret_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encode_session(settings: Settings, payload: dict[str, Any]) -> str:
    return _fernet(settings).encrypt(json.dumps(payload, separators=(",", ":")).encode()).decode()


def _decode_session(settings: Settings, token: str) -> dict[str, Any]:
    try:
        raw = _fernet(settings).decrypt(token.encode())
        return json.loads(raw.decode("utf-8"))
    except (InvalidToken, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid session") from exc


def set_session_cookie(response: Response, settings: Settings, session_data: dict[str, Any]) -> None:
    token = _encode_session(settings, session_data)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.session_secure,
        samesite=settings.session_samesite,
        path="/",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")


async def get_current_user(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise_auth_required()

    try:
        data = _decode_session(settings, token)
    except ValueError:
        clear_session_cookie(response, settings)
        raise_auth_required()

    user_id = str(data.get("user_id", "")).strip()
    issued_at = int(data.get("issued_at", 0) or 0)
    if not user_id or issued_at <= 0 or time.time() - issued_at > settings.session_ttl_seconds:
        clear_session_cookie(response, settings)
        raise_auth_required()

    resources: AppResources = request.app.state.resources
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
        clear_session_cookie(response, settings)
        raise_auth_required("Authenticated account has no matching users row")

    return CurrentUser(
        id=row[0],
        username=row[1] or "Người dùng",
        email=row[2] or "",
        avatar_url=row[3],
    )


def raise_auth_required(message: str = "Yêu cầu đăng nhập để sử dụng Community") -> None:
    # Raising a plain HTTPException in a helper would add another import at every call site.
    from fastapi import HTTPException

    raise HTTPException(status_code=401, detail={"error": "AUTHENTICATION_REQUIRED", "message": message})


def auth_dependency() -> Any:
    return Depends(get_current_user)
