"""Background scheduler for the automation engine.

Runs ``AutomationService.run_engine`` for every known tenant on a
fixed cadence (default: every 5 minutes). The scheduler is opt-in via
the ``AUTOMATION_SCHEDULER_ENABLED`` environment variable — by default
it is ``True`` in non-test environments.

Failures are isolated per tenant so one broken tenant cannot starve
the others. The loop exits cleanly on ``asyncio.CancelledError`` so
FastAPI's lifespan shutdown path is honoured.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.modules.automation.service import AutomationService
from app.modules.companies.models import Empresa

logger = logging.getLogger("ai_sales_agent.automation.scheduler")

DEFAULT_INTERVAL_SECONDS = 300  # 5 min
ENABLED_ENV = "AUTOMATION_SCHEDULER_ENABLED"
INTERVAL_ENV = "AUTOMATION_SCHEDULER_INTERVAL_SECONDS"


def is_enabled() -> bool:
    raw = os.getenv(ENABLED_ENV, "true").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def interval_seconds() -> int:
    try:
        return int(os.getenv(INTERVAL_ENV, str(DEFAULT_INTERVAL_SECONDS)))
    except ValueError:
        return DEFAULT_INTERVAL_SECONDS


async def _list_empresa_ids() -> list:
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Empresa.id)
            result = await session.execute(stmt)
            return [row[0] for row in result.all()]
        except Exception:  # pragma: no cover - resilience
            logger.exception("scheduler: failed to list tenants")
            return []


async def _run_once(loop_label: str) -> int:
    empresa_ids = await _list_empresa_ids()
    if not empresa_ids:
        return 0
    ran = 0
    for empresa_id in empresa_ids:
        async with AsyncSessionLocal() as session:
            try:
                svc = AutomationService(session)
                # Ensure the 7 default rules exist (idempotent)
                await svc.ensure_seeded(empresa_id)
                await svc.run_engine(empresa_id)
                ran += 1
            except Exception:  # pragma: no cover - resilience
                logger.exception(
                    "scheduler: tenant %s failed (%s)", empresa_id, loop_label
                )
    return ran


async def scheduler_loop(stop_event: asyncio.Event) -> None:
    """Run ``run_once`` every ``interval_seconds()`` until ``stop_event`` is set."""
    interval = interval_seconds()
    logger.info("automation scheduler started (interval=%ss)", interval)
    while not stop_event.is_set():
        try:
            ran = await _run_once(f"loop-{datetime.utcnow().isoformat()}")
            if ran:
                logger.info("automation scheduler: ran for %d tenants", ran)
        except asyncio.CancelledError:
            raise
        except Exception:  # pragma: no cover - resilience
            logger.exception("automation scheduler loop error")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue
    logger.info("automation scheduler stopped")


def start_scheduler() -> tuple[asyncio.Task, asyncio.Event] | None:
    """Spawn the scheduler as a background task. Returns ``(task, stop_event)``
    or ``None`` when the scheduler is disabled."""
    if not is_enabled():
        logger.info("automation scheduler disabled via %s", ENABLED_ENV)
        return None
    stop_event = asyncio.Event()
    task = asyncio.create_task(
        scheduler_loop(stop_event), name="automation-scheduler"
    )
    return task, stop_event


__all__ = ["start_scheduler", "scheduler_loop", "is_enabled", "interval_seconds"]
