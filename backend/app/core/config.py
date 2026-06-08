import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

logger = logging.getLogger("ai_sales_agent.config")


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "AI Sales Agent SaaS"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    database_url: str

    redis_url: str = ""

    jwt_issuer: str
    jwt_audience: str
    jwt_algorithm: str = "HS256"
    jwt_secret_key: str
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 512
    openai_temperature: float = 0.7
    openai_timeout_seconds: int = 30
    openai_max_retries: int = 2

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    def check_production_readiness(self) -> list[str]:
        warnings: list[str] = []
        if self.jwt_secret_key and "change-before-production" in self.jwt_secret_key:
            warnings.append("JWT_SECRET_KEY still has the default development value. Generate a new random key for production.")
        if not self.redis_url:
            warnings.append("REDIS_URL is not configured. Rate limiting and caching will use in-memory storage (not suitable for multi-instance production).")
        if self.app_env == "production" and self.backend_cors_origins == "http://localhost:3000":
            warnings.append("BACKEND_CORS_ORIGINS is still set to localhost. Configure your production frontend URL.")
        return warnings


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    for w in settings.check_production_readiness():
        logger.warning("PRODUCTION READINESS: %s", w)
    return settings
