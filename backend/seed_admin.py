"""Crea el primer Super Admin (idempotente).

Uso (desde ``backend/``):
    .venv\\Scripts\\python.exe -m seed_admin [--email ...] [--password ...] [--full-name ...]

Si el email ya existe, no hace nada y termina 0. Por defecto crea
``admin@fashionsales.ai`` con password ``Admin@2024!``.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security.password import hash_password
from app.database.base import Base
from app.database.models import import_all_models
from app.database.session import AsyncSessionLocal, engine
from app.modules.admin.models import SUPER_ADMIN_ROLE, AdminUser

logger = logging.getLogger("ai_sales_agent.seed_admin")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


async def _ensure_schema() -> None:
    import_all_models()
    # We don't auto-create tables — Alembic does. Just verify metadata is consistent.
    _ = Base.metadata


async def _create_super_admin(
    *, email: str, password: str, full_name: str | None
) -> AdminUser:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        existing = (
            await session.execute(select(AdminUser).where(AdminUser.email == email.lower()))
        ).scalar_one_or_none()
        if existing is not None:
            logger.info("Super admin already exists: %s", email)
            return existing

        user = AdminUser(
            email=email.lower(),
            password_hash=hash_password(password),
            full_name=full_name,
            rol=SUPER_ADMIN_ROLE,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(
            "Created super admin: id=%s email=%s env=%s",
            user.id,
            user.email,
            settings.app_env,
        )
        return user


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the first super admin")
    parser.add_argument("--email", default="admin@fashionsales.ai")
    parser.add_argument("--password", default="Admin@2024!")
    parser.add_argument("--full-name", default="Platform Super Admin")
    return parser.parse_args()


async def _main() -> int:
    args = _parse_args()
    await _ensure_schema()
    await _create_super_admin(
        email=args.email, password=args.password, full_name=args.full_name
    )
    await engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
