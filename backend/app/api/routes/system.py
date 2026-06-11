"""
Enterprise system status endpoint.

GET /system/status → full health report for monitoring and dashboards.

Returns:
  - Database connectivity
  - Redis connectivity
  - OpenAI API status
  - WhatsApp integration status
  - Storage (disk usage)
  - Application uptime
  - Version info
  - Active error count (last 24h)
"""

import logging
import os
import shutil
import time
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.error_ids import get_recent_errors
from app.core.redis import get_redis
from app.database.session import check_database_connection

logger = logging.getLogger("ai_sales_agent.system")
router = APIRouter()

_start_time: float = time.time()
_whatsapp_status: str = "unknown"


class SystemStatusResponse(BaseModel):
    status: str
    version: str
    environment: str
    uptime_seconds: float
    database: str
    redis: str
    openai: str
    whatsapp: str
    storage: dict[str, object]
    errors_24h: int
    service: str


def _check_storage() -> dict[str, object]:
    try:
        total, used, free = shutil.disk_usage(Path.cwd())
        return {
            "total_gb": round(total / (1024**3), 1),
            "used_gb": round(used / (1024**3), 1),
            "free_gb": round(free / (1024**3), 1),
            "percent_used": round(used / total * 100, 1),
        }
    except Exception:
        return {"error": "Unable to check disk usage"}


@router.get("/status", response_model=SystemStatusResponse)
async def system_status() -> SystemStatusResponse:
    settings = get_settings()

    db_ok = await check_database_connection()

    redis_status = "not_configured"
    if settings.redis_url:
        try:
            r = await get_redis()
            if r is not None:
                await r.ping()
                redis_status = "connected"
            else:
                redis_status = "error"
        except Exception:
            redis_status = "error"

    openai_status = "not_configured"
    openai_api_key = os.environ.get("OPENAI_API_KEY", settings.openai_api_key)
    if openai_api_key:
        openai_status = "configured"

    whatsapp_status = _whatsapp_status or "not_configured"
    if settings.whatsapp_encryption_key:
        whatsapp_status = "configured"

    recent_errors = [e for e in get_recent_errors() if isinstance(e.get("timestamp"), str)]

    return SystemStatusResponse(
        status="healthy" if db_ok else "degraded",
        version="0.1.0",
        environment=settings.app_env,
        uptime_seconds=round(time.time() - _start_time, 2),
        database="connected" if db_ok else "disconnected",
        redis=redis_status,
        openai=openai_status,
        whatsapp=whatsapp_status,
        storage=_check_storage(),
        errors_24h=len(recent_errors),
        service="ai-sales-agent-saas-api",
    )
