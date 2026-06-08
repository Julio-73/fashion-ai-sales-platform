import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.log_config import configure_logging
from app.core.middleware import register_middleware
from app.database.session import check_database_connection

configure_logging()
logger = logging.getLogger("ai_sales_agent")


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        logger.info("Starting %s v0.1.0", settings.app_name)
        logger.info("Environment: %s", settings.app_env)
        if settings.app_env != "local":
            for w in settings.check_production_readiness():
                logger.warning("PRODUCTION READINESS: %s", w)
        if not await check_database_connection():
            logger.warning(
                "Continuing startup despite DB connection failure. "
                "API will return 500 on database-dependent endpoints."
            )
        # Register decoupled domain event listeners (inventory reacts to
        # order.confirmed / order.cancelled).
        from app.modules.inventory.listeners import register_inventory_listener

        register_inventory_listener()
        # Start the automation engine scheduler (additive).
        from app.modules.automation.scheduler import start_scheduler

        scheduler_handle = start_scheduler()
        try:
            yield
        finally:
            if scheduler_handle is not None:
                _task, stop_event = scheduler_handle
                stop_event.set()
                try:
                    await _task
                except Exception:  # pragma: no cover - shutdown
                    logger.exception("automation scheduler shutdown error")
            from app.modules.inventory.listeners import unregister_inventory_listener

            unregister_inventory_listener()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )

    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


try:
    app = create_app()
except Exception as exc:
    logger.critical("Failed to create application: %s", exc)
    sys.exit(1)

