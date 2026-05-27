from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.config import AISettings
from app.ai.providers.openai_provider import OpenAIProvider, OpenAIProviderError


@pytest.fixture
def configured_settings() -> AISettings:
    return AISettings(
        openai_api_key="sk-test-key",
        openai_model="gpt-4o-mini",
        openai_max_tokens=100,
        openai_temperature=0.5,
        openai_timeout_seconds=5,
        openai_max_retries=0,
    )


@pytest.fixture
def unconfigured_settings() -> AISettings:
    return AISettings(openai_api_key="")


class TestOpenAIProvider:
    def test_init_configured(self, configured_settings):
        provider = OpenAIProvider(settings=configured_settings)
        assert provider.is_configured is True

    def test_init_unconfigured(self, unconfigured_settings):
        provider = OpenAIProvider(settings=unconfigured_settings)
        assert provider.is_configured is False

    def test_default_is_configured(self):
        provider = OpenAIProvider()
        assert provider.is_configured is False

    @pytest.mark.asyncio
    async def test_generate_raises_when_not_configured(self, unconfigured_settings):
        provider = OpenAIProvider(settings=unconfigured_settings)
        with pytest.raises(OpenAIProviderError, match="API key not configured"):
            await provider.generate(
                system_prompt="system",
                user_message="hello",
            )

    @pytest.mark.asyncio
    async def test_generate_success(self, configured_settings):
        provider = OpenAIProvider(settings=configured_settings)

        mock_message = MagicMock()
        mock_message.content = "Hola, soy el asistente virtual"

        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 42

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = mock_usage

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            result = await provider.generate(
                system_prompt="Eres un asistente",
                user_message="Hola",
                temperature=0.5,
                max_tokens=100,
            )

        assert result == "Hola, soy el asistente virtual"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asistente"},
                {"role": "user", "content": "Hola"},
            ],
            temperature=0.5,
            max_tokens=100,
        )

    @pytest.mark.asyncio
    async def test_generate_uses_default_temperature_and_tokens(self, configured_settings):
        provider = OpenAIProvider(settings=configured_settings)

        mock_message = MagicMock()
        mock_message.content = "Respuesta"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"
        mock_usage = MagicMock()
        mock_usage.total_tokens = 10
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = mock_usage

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            result = await provider.generate(
                system_prompt="system",
                user_message="msg",
            )

        assert result == "Respuesta"
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": "msg"},
            ],
            temperature=0.5,
            max_tokens=100,
        )

    @pytest.mark.asyncio
    async def test_generate_handles_api_error(self, configured_settings):
        provider = OpenAIProvider(settings=configured_settings)

        mock_client = AsyncMock()

        import openai

        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.APIError(
                message="Bad gateway",
                request=MagicMock(),
                body=None,
            )
        )

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(OpenAIProviderError, match="OpenAI API error"):
                await provider.generate(
                    system_prompt="system",
                    user_message="msg",
                )

    @pytest.mark.asyncio
    async def test_generate_handles_rate_limit(self, configured_settings):
        provider = OpenAIProvider(settings=configured_settings)

        mock_client = AsyncMock()

        import httpx
        import openai

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.headers = {"x-request-id": "req_123", "content-type": "application/json"}

        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.RateLimitError(
                message="Rate limited",
                response=mock_response,
                body=None,
            )
        )

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(OpenAIProviderError, match="Rate limit exceeded"):
                await provider.generate(
                    system_prompt="system",
                    user_message="msg",
                )

    @pytest.mark.asyncio
    async def test_generate_handles_timeout(self, configured_settings):
        provider = OpenAIProvider(settings=configured_settings)

        mock_client = AsyncMock()

        import httpx
        import openai

        mock_request = MagicMock(spec=httpx.Request)

        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.APITimeoutError(request=mock_request)
        )

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            with pytest.raises(OpenAIProviderError, match="Request timed out"):
                await provider.generate(
                    system_prompt="system",
                    user_message="msg",
                )

    @pytest.mark.asyncio
    async def test_generate_strips_whitespace(self, configured_settings):
        provider = OpenAIProvider(settings=configured_settings)

        mock_message = MagicMock()
        mock_message.content = "  Hola, soy el asistente  \n"

        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 10

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = mock_usage

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            result = await provider.generate(
                system_prompt="system",
                user_message="msg",
            )

        assert result == "Hola, soy el asistente"

    @pytest.mark.asyncio
    async def test_generate_handles_empty_content(self, configured_settings):
        provider = OpenAIProvider(settings=configured_settings)

        mock_message = MagicMock()
        mock_message.content = None

        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"

        mock_usage = MagicMock()
        mock_usage.total_tokens = 5

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4o-mini"
        mock_response.usage = mock_usage

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("openai.AsyncOpenAI", return_value=mock_client):
            result = await provider.generate(
                system_prompt="system",
                user_message="msg",
            )

        assert result == ""

    def test_default_ai_settings_values(self):
        settings = AISettings()
        assert settings.openai_api_key == ""
        assert settings.openai_model == "gpt-4o-mini"
        assert settings.openai_max_tokens == 512
        assert settings.openai_temperature == 0.7
        assert settings.openai_timeout_seconds == 30
        assert settings.openai_max_retries == 2
        assert "agente humano" in settings.openai_fallback_response

    def test_ai_settings_custom_values(self):
        settings = AISettings(
            openai_api_key="sk-custom",
            openai_model="gpt-4",
            openai_max_tokens=1024,
            openai_temperature=0.3,
        )
        assert settings.openai_api_key == "sk-custom"
        assert settings.openai_model == "gpt-4"
        assert settings.openai_max_tokens == 1024
        assert settings.openai_temperature == 0.3
