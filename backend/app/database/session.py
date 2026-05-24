import logging
from collections.abc import AsyncGenerator

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

logger = logging.getLogger("ai_sales_agent.database")

settings = get_settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def check_database_connection() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        logger.info("Database connection OK - %s", settings.database_url.replace("://", "://***:***@"))
        return True
    except OperationalError as exc:
        logger.critical("Database connection FAILED: %s", exc)
        logger.critical(
            "Ensure PostgreSQL is running on port 5432 and database '%s' exists. "
            "Check backend/.env for DATABASE_URL.",
            settings.database_url.rstrip("/").split("/")[-1],
        )
        return False
    except Exception as exc:
        logger.critical("Unexpected database error: %s", exc)
        return False


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except BaseException:
            await session.rollback()
            raise

