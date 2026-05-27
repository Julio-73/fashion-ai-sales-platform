import logging
from typing import Literal

import openai

from app.ai.config import AISettings

logger = logging.getLogger("ai_sales_agent.ai.providers.openai")

ReplyIntent = Literal["sales", "support", "upsell", "negotiation", "recovery"]


class OpenAIProviderError(Exception):
    pass


class OpenAIProvider:
    def __init__(self, settings: AISettings | None = None) -> None:
        self._settings = settings or AISettings()
        self._configured = bool(self._settings.openai_api_key)

    @property
    def is_configured(self) -> bool:
        return self._configured

    async def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        if not self._configured:
            raise OpenAIProviderError("OpenAI API key not configured")

        client = openai.AsyncOpenAI(
            api_key=self._settings.openai_api_key,
            timeout=self._settings.openai_timeout_seconds,
            max_retries=self._settings.openai_max_retries,
        )

        try:
            response = await client.chat.completions.create(
                model=self._settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature if temperature is not None else self._settings.openai_temperature,
                max_tokens=max_tokens if max_tokens is not None else self._settings.openai_max_tokens,
            )
        except openai.RateLimitError as exc:
            logger.error("OpenAI rate limit exceeded: %s", exc)
            raise OpenAIProviderError(f"Rate limit exceeded: {exc}") from exc
        except openai.APITimeoutError as exc:
            logger.error("OpenAI request timed out: %s", exc)
            raise OpenAIProviderError(f"Request timed out: {exc}") from exc
        except openai.APIError as exc:
            logger.error("OpenAI API error: %s", exc)
            raise OpenAIProviderError(f"OpenAI API error: {exc}") from exc
        except Exception as exc:
            logger.error("Unexpected OpenAI error: %s", exc)
            raise OpenAIProviderError(f"Unexpected error: {exc}") from exc

        choice = response.choices[0]
        content = choice.message.content or ""

        logger.info(
            "OpenAI response: model=%s, tokens=%d, finish_reason=%s",
            response.model,
            response.usage.total_tokens if response.usage else 0,
            choice.finish_reason,
        )

        return content.strip()
