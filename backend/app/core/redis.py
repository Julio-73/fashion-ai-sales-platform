"""Async Redis connection manager for distributed rate limiting and caching.

Gracefully falls back to in-memory stores when Redis is not configured,
allowing local development without a Redis server.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger("ai_sales_agent.redis")

_redis: Any = None


async def get_redis() -> Any | None:
    global _redis
    if _redis is not None:
        return _redis
    settings = get_settings()
    if not settings.redis_url:
        return None
    try:
        import redis.asyncio as aioredis

        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        await _redis.ping()
        logger.info("Connected to Redis at %s", settings.redis_url)
        return _redis
    except Exception:
        logger.warning("Redis unavailable — falling back to in-memory stores")
        _redis = None
        return None


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        try:
            await _redis.close()
        except Exception:
            pass
        _redis = None
        logger.info("Redis connection closed")
