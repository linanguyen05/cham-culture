"""Async gateway to Supabase Auth (GoTrue) and Supabase Storage over HTTPS.

Uses the service-role key. Kept thin and dependency-light (httpx only) so the
whole app stays async and we avoid the sync supabase-py client.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.config import Settings


class SupabaseError(Exception):
    pass


class AuthConflictError(SupabaseError):
    """Email already registered."""


class SupabaseGateway:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self.settings = settings
        self.client = client
        self.base = settings.api_base
        self.key = settings.supabase_service_role_key
        self.bucket = settings.supabase_storage_bucket

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {"apikey": self.key, "Authorization": f"Bearer {self.key}"}

    # --- Auth (GoTrue) ------------------------------------------------------- #
    async def admin_create_user(self, email: str, password: str) -> dict[str, Any]:
        r = await self.client.post(
            f"{self.base}/auth/v1/admin/users",
            headers=self._auth_headers,
            json={"email": email, "password": password, "email_confirm": True},
            timeout=20,
        )
        if r.status_code in (200, 201):
            return r.json()
        body = _safe_json(r)
        msg = (body.get("msg") or body.get("message") or body.get("error_description") or "").lower()
        if r.status_code in (400, 409, 422) and ("already" in msg or "exist" in msg or "registered" in msg):
            raise AuthConflictError(msg or "email already registered")
        raise SupabaseError(f"admin_create_user failed: {r.status_code} {body}")

    async def sign_in_password(self, email: str, password: str) -> dict[str, Any] | None:
        r = await self.client.post(
            f"{self.base}/auth/v1/token",
            params={"grant_type": "password"},
            headers={"apikey": self.key, "Content-Type": "application/json"},
            json={"email": email, "password": password},
            timeout=20,
        )
        if r.status_code == 200:
            return r.json().get("user")
        if r.status_code in (400, 401, 403):
            return None
        raise SupabaseError(f"sign_in_password failed: {r.status_code} {_safe_json(r)}")

    # --- Storage ------------------------------------------------------------- #
    async def ensure_bucket(self) -> None:
        r = await self.client.get(
            f"{self.base}/storage/v1/bucket/{self.bucket}", headers=self._auth_headers, timeout=20
        )
        if r.status_code == 200:
            return
        create = await self.client.post(
            f"{self.base}/storage/v1/bucket",
            headers=self._auth_headers,
            json={
                "id": self.bucket,
                "name": self.bucket,
                "public": self.settings.supabase_storage_public,
            },
            timeout=20,
        )
        if create.status_code not in (200, 201):
            # A concurrent create or "already exists" is fine.
            body = _safe_json(create)
            if "exist" not in str(body).lower():
                raise SupabaseError(f"ensure_bucket failed: {create.status_code} {body}")

    async def upload_object(self, path: str, data: bytes, content_type: str) -> str:
        enc_path = quote(path)
        r = await self.client.post(
            f"{self.base}/storage/v1/object/{self.bucket}/{enc_path}",
            headers={**self._auth_headers, "Content-Type": content_type, "x-upsert": "true"},
            content=data,
            timeout=60,
        )
        if r.status_code not in (200, 201):
            raise SupabaseError(f"upload_object failed: {r.status_code} {_safe_json(r)}")
        return self.public_url(path)

    async def delete_object_by_url(self, url: str) -> None:
        path = self._path_from_url(url)
        if path is None:
            return
        await self.client.request(
            "DELETE",
            f"{self.base}/storage/v1/object/{self.bucket}/{quote(path)}",
            headers=self._auth_headers,
            timeout=30,
        )

    def public_url(self, path: str) -> str:
        return f"{self.base}/storage/v1/object/public/{self.bucket}/{quote(path)}"

    def _path_from_url(self, url: str) -> str | None:
        marker = f"/storage/v1/object/public/{self.bucket}/"
        if marker in url:
            return url.split(marker, 1)[1]
        return None


def _safe_json(r: httpx.Response) -> dict[str, Any]:
    try:
        data = r.json()
        return data if isinstance(data, dict) else {"raw": data}
    except Exception:
        return {"raw": r.text[:300]}
