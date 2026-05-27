from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_live.repository import ConversationAIRepository
from app.ai_live.services.handoff_service import HandoffService
from app.ai_live.services.insights_service import AIInsightsService
from app.ai_live.services.suggestions_service import AISuggestionsService
from app.ai_live.orchestrators.ai_live_orchestrator import AILiveOrchestrator
from app.ai.services.llm_service import LLMService
from app.database.session import get_db_session


async def get_ai_live_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ConversationAIRepository:
    return ConversationAIRepository(session=session)


async def get_handoff_service() -> HandoffService:
    return HandoffService()


async def get_llm_service() -> LLMService:
    return LLMService()


async def get_ai_suggestions_service(
    repository: Annotated[ConversationAIRepository, Depends(get_ai_live_repository)],
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
    handoff_service: Annotated[HandoffService, Depends(get_handoff_service)],
) -> AISuggestionsService:
    return AISuggestionsService(
        repository=repository,
        llm_service=llm_service,
        handoff_service=handoff_service,
    )


async def get_ai_insights_service(
    repository: Annotated[ConversationAIRepository, Depends(get_ai_live_repository)],
    llm_service: Annotated[LLMService, Depends(get_llm_service)],
    handoff_service: Annotated[HandoffService, Depends(get_handoff_service)],
) -> AIInsightsService:
    return AIInsightsService(
        repository=repository,
        llm_service=llm_service,
        handoff_service=handoff_service,
    )


async def get_ai_live_orchestrator(
    repository: Annotated[ConversationAIRepository, Depends(get_ai_live_repository)],
    suggestions_service: Annotated[AISuggestionsService, Depends(get_ai_suggestions_service)],
    insights_service: Annotated[AIInsightsService, Depends(get_ai_insights_service)],
    handoff_service: Annotated[HandoffService, Depends(get_handoff_service)],
) -> AILiveOrchestrator:
    return AILiveOrchestrator(
        repository=repository,
        suggestions_service=suggestions_service,
        insights_service=insights_service,
        handoff_service=handoff_service,
    )
