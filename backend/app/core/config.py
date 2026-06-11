import logging
import sys
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config import production

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"

logger = logging.getLogger("ai_sales_agent.config")


class DatabasePoolSettings(BaseSettings):
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")


class ServerSettings(BaseSettings):
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    timeout_keepalive: int = 5

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")


class Settings(BaseSettings):
    app_env: str = "local"
    app_name: str = "AI Sales Agent SaaS"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    database_url: str

    redis_url: str = ""

    jwt_issuer: str = "ai-sales-agent-saas"
    jwt_audience: str = "ai-sales-agent-dashboard"
    jwt_algorithm: str = "HS256"
    jwt_secret_key: str
    admin_jwt_secret_key: str = ""
    whatsapp_encryption_key: str = ""
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

    def validate_critical(self) -> list[str]:
        errors: list[str] = []
        if not self.database_url:
            errors.append("DATABASE_URL is not set. Application cannot start without a database.")
        if not self.jwt_secret_key or "change-this-to" in self.jwt_secret_key:
            errors.append("JWT_SECRET_KEY is missing or still has the default placeholder value. Generate a random 64-char secret.")
        if self.app_env == "production":
            if not self.admin_jwt_secret_key or self.admin_jwt_secret_key == self.jwt_secret_key:
                errors.append("ADMIN_JWT_SECRET_KEY must be set and different from JWT_SECRET_KEY in production.")
            if not self.whatsapp_encryption_key:
                errors.append("WHATSAPP_ENCRYPTION_KEY is required in production for secure token storage.")
            if not self.redis_url:
                errors.append("REDIS_URL is required in production for multi-instance deployments.")
            if not self.openai_api_key:
                errors.append("OPENAI_API_KEY is required in production for AI Sales Agent features.")
            if "localhost" in self.backend_cors_origins:
                errors.append("BACKEND_CORS_ORIGINS must point to your production frontend URL, not localhost.")
        return errors

    def check_warnings(self) -> list[str]:
        warnings: list[str] = []
        if self.jwt_secret_key and "change-before-production" in self.jwt_secret_key:
            warnings.append("JWT_SECRET_KEY still has the default development value. Generate a new random key for production.")
        if not self.admin_jwt_secret_key:
            warnings.append("ADMIN_JWT_SECRET_KEY is not configured. Admin JWT shares the same secret as user JWT — set a separate key for production.")
        if not self.whatsapp_encryption_key:
            warnings.append("WHATSAPP_ENCRYPTION_KEY is not configured. WhatsApp access tokens will be stored in plaintext.")
        if not self.redis_url:
            warnings.append("REDIS_URL is not configured. Rate limiting and caching will use in-memory storage (not suitable for multi-instance production).")
        if not self.openai_api_key:
            warnings.append("OPENAI_API_KEY is not configured. AI features will be unavailable.")
        if self.app_env == "production" and "localhost" in self.backend_cors_origins:
            warnings.append("BACKEND_CORS_ORIGINS is still set to localhost. Configure your production frontend URL.")
        return warnings


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    # Apply production overrides
    if settings.app_env == "production":
        if hasattr(production, "TIMEOUTS"):
            settings.openai_timeout_seconds = production.TIMEOUTS.get("openai_request", 30)
        if hasattr(production, "CACHE"):
            pass  # cache prefix is internal; timeout is managed by app
        logger.info("Production configuration loaded: workers=%s, pool_size=%s",
                     getattr(production, "WORKERS", 4),
                     production.DATABASE_POOL.get("pool_size", 10) if hasattr(production, "DATABASE_POOL") else 10)

    errors = settings.validate_critical()
    if errors:
        for err in errors:
            logger.critical("CONFIG ERROR: %s", err)
        print("=" * 70, file=sys.stderr)
        print("FATAL: Configuration errors detected. Cannot start application.", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        sys.exit(1)

    for w in settings.check_warnings():
        logger.warning("CONFIG: %s", w)

    return settings


@lru_cache
def get_db_pool_settings() -> DatabasePoolSettings:
    pool = DatabasePoolSettings()
    from app.config import production as prod
    if hasattr(prod, "DATABASE_POOL"):
        cfg = prod.DATABASE_POOL
        pool.db_pool_size = cfg.get("pool_size", pool.db_pool_size)
        pool.db_max_overflow = cfg.get("max_overflow", pool.db_max_overflow)
        pool.db_pool_timeout = cfg.get("pool_timeout", pool.db_pool_timeout)
        pool.db_pool_recycle = cfg.get("pool_recycle", pool.db_pool_recycle)
    return pool


@lru_cache
def get_server_settings() -> ServerSettings:
    svr = ServerSettings()
    from app.config import production as prod
    if hasattr(prod, "WORKERS"):
        svr.workers = prod.WORKERS
    return svr
