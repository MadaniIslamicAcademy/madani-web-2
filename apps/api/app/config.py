from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    environment: str = "development"
    app_name: str = "Madani Social Automation Platform"
    timezone: str = "Asia/Karachi"
    frontend_url: str = "http://localhost:3000"
    api_public_url: str = "http://localhost:8000"

    database_url: str = "sqlite:///./madani_social.sqlite3"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = Field(default="development-secret-change-me-use-32-bytes", min_length=16)
    token_encryption_key: str = ""
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    cookie_secure: bool = False
    bootstrap_admin_email: str = "admin@madaniislamicacademy.com"
    bootstrap_admin_password: str = "change-this-password-now"

    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"
    ai_provider: str = "openai"

    social_publish_mode: str = "mock"
    max_publish_retries: int = 3

    meta_graph_version: str = "v24.0"
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_redirect_uri: str = "http://localhost:8000/api/v1/oauth/meta/callback"
    whatsapp_verify_token: str = "change-whatsapp-verify-token"

    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/api/v1/oauth/linkedin/callback"
    linkedin_version: str = "202607"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/oauth/google/callback"

    tiktok_client_key: str = ""
    tiktok_client_secret: str = ""
    tiktok_redirect_uri: str = "http://localhost:8000/api/v1/oauth/tiktok/callback"

    x_client_id: str = ""
    x_client_secret: str = ""
    x_redirect_uri: str = "http://localhost:8000/api/v1/oauth/x/callback"

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
