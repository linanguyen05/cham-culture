from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from app.config import Settings
from app.extensions import AppResources


class AuthService:
    """Server-side adapter for Supabase Auth REST endpoints."""

    def __init__(self, resources: AppResources, settings: Settings) -> None:
        self.resources = resources
        self.settings = settings

    async def sign_in(self, email: str, password: str) -> dict[str, Any]:
        response = await self.resources.http_client.post(
            f"{self.settings.supabase_url.rstrip('/')}/auth/v1/token",
            params={"grant_type": "password"},
            headers={"apikey": self.settings.supabase_anon_key},
            json={"email": email, "password": password},
        )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=401,
                detail={"error": "AUTHENTICATION_REQUIRED", "message": "Email hoặc mật khẩu không đúng."},
            )
        return response.json()

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        response = await self.resources.http_client.post(
            f"{self.settings.supabase_url.rstrip('/')}/auth/v1/token",
            params={"grant_type": "refresh_token"},
            headers={"apikey": self.settings.supabase_anon_key},
            json={"refresh_token": refresh_token},
        )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=401,
                detail={"error": "AUTHENTICATION_REQUIRED", "message": "Phiên đăng nhập đã hết hạn."},
            )
        return response.json()

    @staticmethod
    def build_session_payload(auth_payload: dict[str, Any], user_row: dict[str, Any]) -> dict[str, Any]:
        expires_in = int(auth_payload.get("expires_in", 3600))
        return {
            "user_id": str(user_row["id"]),
            "email": user_row.get("email", ""),
            "access_token": auth_payload["access_token"],
            "refresh_token": auth_payload.get("refresh_token", ""),
            "access_expires_at": int(datetime.now(timezone.utc).timestamp()) + expires_in,
            "issued_at": int(datetime.now(timezone.utc).timestamp()),
        }
