"""Application configuration.

Loaded from environment variables / a local ``.env`` file. Unlike the original
Supabase-oriented backend, this build runs fully locally: SQLite for data and
the local filesystem for uploaded media. Cloud settings are therefore optional
and only consulted if you later wire an external provider back in.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# backend/ directory (parent of the app package). Used to resolve relative paths.
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Cham Culture Community API"
    environment: str = "development"

    # A 32+ char default keeps the server runnable out of the box for local dev.
    # ALWAYS override SECRET_KEY via .env in any shared or production environment.
    secret_key: str = Field(
        default="cham-culture-dev-secret-key-change-me!", min_length=32
    )
    session_cookie_name: str = "cham_community_session"
    session_ttl_seconds: int = Field(default=60 * 60 * 24 * 7, ge=300)
    session_secure: bool = False
    session_samesite: str = "lax"

    # --- Local storage backends -------------------------------------------------
    database_path: str = "data/cham_culture.db"
    upload_dir: str = "uploads"
    # Location of the canonical frontend/ folder that this backend serves.
    frontend_dir: str = str(PROJECT_ROOT / "frontend")

    # --- Content limits ---------------------------------------------------------
    max_upload_images: int = Field(default=4, ge=1, le=8)
    max_image_size_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    max_content_length: int = Field(default=5000, ge=1)
    max_comment_length: int = Field(default=1000, ge=1)
    max_share_length: int = Field(default=2000, ge=1)

    # --- CSRF / CORS ------------------------------------------------------------
    frontend_origins: list[str] = Field(default_factory=list)
    allow_missing_origin_for_unsafe_methods: bool = True

    # --- Rate limits ------------------------------------------------------------
    rate_limit_storage_uri: str = "memory://"
    rate_limit_login: str = "10/minute"
    rate_limit_post: str = "20/minute"
    rate_limit_comment: str = "40/minute"
    rate_limit_like: str = "120/minute"

    @field_validator("frontend_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]
        return value  # type: ignore[return-value]

    @field_validator("session_samesite")
    @classmethod
    def validate_samesite(cls, value: str) -> str:
        value = value.lower()
        if value not in {"lax", "strict", "none"}:
            raise ValueError("SESSION_SAMESITE must be lax, strict, or none")
        return value

    # --- Resolved absolute paths ------------------------------------------------
    @property
    def database_file(self) -> Path:
        path = Path(self.database_path)
        return path if path.is_absolute() else BACKEND_DIR / path

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        return path if path.is_absolute() else BACKEND_DIR / path

    @property
    def frontend_path(self) -> Path:
        return Path(self.frontend_dir)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
