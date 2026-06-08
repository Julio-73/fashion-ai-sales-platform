import logging
import time

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.database.session import check_database_connection

logger = logging.getLogger("ai_sales_agent")
router = APIRouter()

_start_time: float = time.time()


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    uptime_seconds: float
    database: str
    redis: str
    openai: str


@router.get("/health", response_model=HealthCheckResponse)
async def health() -> HealthCheckResponse:
    settings = get_settings()

    db_ok = await check_database_connection()

    redis_status = "not_configured"
    if settings.redis_url:
        try:
            redis_status = "connected"
        except Exception:
            redis_status = "error"

    openai_status = "not_configured"
    if settings.openai_api_key:
        try:
            openai_status = "configured"
        except Exception:
            openai_status = "error"

    return HealthCheckResponse(
        status="ok" if db_ok else "degraded",
        service="ai-sales-agent-saas-api",
        version="0.1.0",
        environment=settings.app_env,
        uptime_seconds=round(time.time() - _start_time, 2),
        database="connected" if db_ok else "disconnected",
        redis=redis_status,
        openai=openai_status,
    )
