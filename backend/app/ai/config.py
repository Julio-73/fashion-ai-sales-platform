from functools import lru_cache

from pydantic_settings import BaseSettings


class AISettings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 512
    openai_temperature: float = 0.7
    openai_timeout_seconds: int = 30
    openai_max_retries: int = 2
    openai_fallback_response: str = (
        "Gracias por tu mensaje. En este momento no puedo procesar tu solicitud, "
        "pero un agente humano te atenderá en breve."
    )

    model_config = {"env_prefix": "", "extra": "ignore"}


@lru_cache
def get_ai_settings() -> AISettings:
    return AISettings()
