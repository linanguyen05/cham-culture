"""Application configuration (Supabase / PostgreSQL).

Data lives in the project's Supabase PostgreSQL (accessed via psycopg); auth uses
Supabase Auth (GoTrue) and media uses Supabase Storage. Secrets come from a local
``.env`` (git-ignored). See ``.env.example``.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Cham Culture Community API"
    environment: str = "development"

    secret_key: str = Field(min_length=32)
    session_cookie_name: str = "cham_community_session"
    session_ttl_seconds: int = Field(default=60 * 60 * 24 * 7, ge=300)
    session_secure: bool = False
    session_samesite: str = "lax"

    # --- Supabase ---------------------------------------------------------------
    supabase_url: str
    supabase_project_ref: str = ""
    supabase_service_role_key: str
    supabase_anon_key: str = ""
    supabase_db_password: str = ""
    supabase_storage_bucket: str = "community-images"
    supabase_storage_public: bool = True

    # Optional explicit connection string; otherwise derived from ref + password.
    database_url: str = ""
    database_min_size: int = Field(default=1, ge=1)
    database_max_size: int = Field(default=10, ge=1)

    # --- Frontend served by this backend ---------------------------------------
    frontend_dir: str = str(PROJECT_ROOT / "frontend")

    # --- Content limits ---------------------------------------------------------
    max_upload_images: int = Field(default=4, ge=1, le=8)
    max_image_size_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    max_content_length: int = Field(default=5000, ge=1)
    max_comment_length: int = Field(default=1000, ge=1)
    max_share_length: int = Field(default=2000, ge=1)

    # --- CSRF / CORS ------------------------------------------------------------
    # Parsed from a comma-separated string to avoid pydantic-settings treating a
    # list field as JSON in .env.
    frontend_origins_raw: str = Field(default="", validation_alias="FRONTEND_ORIGINS")
    allow_missing_origin_for_unsafe_methods: bool = True

    # --- Rate limits ------------------------------------------------------------
    rate_limit_storage_uri: str = "memory://"
    rate_limit_login: str = "10/minute"
    rate_limit_post: str = "20/minute"
    rate_limit_comment: str = "40/minute"
    rate_limit_like: str = "120/minute"

    @field_validator("session_samesite")
    @classmethod
    def validate_samesite(cls, value: str) -> str:
        value = value.lower()
        if value not in {"lax", "strict", "none"}:
            raise ValueError("SESSION_SAMESITE must be lax, strict, or none")
        return value

    @model_validator(mode="after")
    def _derive_ref(self) -> "Settings":
        if not self.supabase_project_ref and self.supabase_url:
            host = self.supabase_url.split("//", 1)[-1]
            self.supabase_project_ref = host.split(".", 1)[0]
        return self

    @property
    def frontend_origins(self) -> list[str]:
        return [i.strip().rstrip("/") for i in self.frontend_origins_raw.split(",") if i.strip()]

    @property
    def api_base(self) -> str:
        return self.supabase_url.rstrip("/")

    @property
    def db_conninfo(self) -> str:
        """psycopg connection string. Prefer DATABASE_URL if provided, else build
        the direct Supabase connection from project ref + DB password."""
        if self.database_url:
            return self.database_url
        return (
            f"host=db.{self.supabase_project_ref}.supabase.co "
            f"port=5432 dbname=postgres user=postgres "
            f"password={self.supabase_db_password} sslmode=require"
        )

    @property
    def frontend_path(self) -> Path:
        return Path(self.frontend_dir)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
