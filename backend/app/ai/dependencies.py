from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.ai.config import get_ai_settings
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.services.ai_service import AIService
from app.ai.services.llm_service import LLMService
from app.database.session import get_db_session


async def get_openai_provider() -> OpenAIProvider:
    return OpenAIProvider(settings=get_ai_settings())


async def get_llm_service() -> LLMService:
    return LLMService()


async def get_ai_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AIService:
    return AIService(session=session)
