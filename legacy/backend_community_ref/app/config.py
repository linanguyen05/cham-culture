from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded exclusively from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Cham Culture Community API"
    environment: str = "development"
    secret_key: str = Field(min_length=32)
    session_cookie_name: str = "cham_community_session"
    session_ttl_seconds: int = Field(default=60 * 60 * 24 * 7, ge=300)
    session_secure: bool = False
    session_samesite: str = "lax"

    database_url: str = Field(min_length=1)
    database_min_size: int = Field(default=2, ge=1)
    database_max_size: int = Field(default=10, ge=1)

    supabase_url: str = Field(min_length=1)
    supabase_service_role_key: str = Field(min_length=1)
    supabase_anon_key: str = Field(min_length=1)
    supabase_storage_bucket: str = "community-images"
    supabase_storage_public: bool = True

    max_upload_images: int = Field(default=4, ge=1, le=4)
    max_image_size_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    max_content_length: int = Field(default=5000, ge=1)
    max_comment_length: int = Field(default=1000, ge=1)
    max_share_length: int = Field(default=2000, ge=1)

    frontend_origins: list[str] = Field(default_factory=list)
    allow_missing_origin_for_unsafe_methods: bool = True

    rate_limit_storage_uri: str = "memory://"
    rate_limit_login: str = "5/minute"
    rate_limit_post: str = "10/minute"
    rate_limit_comment: str = "30/minute"
    rate_limit_like: str = "60/minute"

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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
