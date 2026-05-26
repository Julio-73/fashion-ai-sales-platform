

from app.ai.services.ai_service import AIService


async def get_ai_service() -> AIService:
    return AIService()
