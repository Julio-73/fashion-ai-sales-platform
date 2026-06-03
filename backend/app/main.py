import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.middleware import register_middleware
from app.database.session import check_database_connection

logger = logging.getLogger("ai_sales_agent")


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        logger.info("Starting %s v0.1.0", settings.app_name)
        logger.info("Environment: %s", settings.app_env)
        if not await check_database_connection():
            logger.warning(
                "Continuing startup despite DB connection failure. "
                "API will return 500 on database-dependent endpoints."
            )
        # Register decoupled domain event listeners (inventory reacts to
        # order.confirmed / order.cancelled).
        from app.modules.inventory.listeners import register_inventory_listener

        register_inventory_listener()
        yield
        from app.modules.inventory.listeners import unregister_inventory_listener

        unregister_inventory_listener()

    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    register_middleware(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


try:
    app = create_app()
except Exception as exc:
    logger.critical("Failed to create application: %s", exc)
    sys.exit(1)

