from app.ai.config import get_ai_settings
from app.ai.providers.openai_provider import OpenAIProvider
from app.ai.services.ai_service import AIService
from app.ai.services.llm_service import LLMService


async def get_openai_provider() -> OpenAIProvider:
    return OpenAIProvider(settings=get_ai_settings())


async def get_llm_service() -> LLMService:
    return LLMService()


async def get_ai_service() -> AIService:
    return AIService()
