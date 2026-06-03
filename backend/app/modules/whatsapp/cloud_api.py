"""Thin async client for the Meta WhatsApp Business Cloud API.

The Cloud API is a JSON over HTTPS API. We only need two operations:

* ``send_text_message`` — POST to ``/{phone_number_id}/messages``
* ``parse_webhook_payload`` — defensive normalizer that pulls inbound
  messages out of the verbose Meta envelope.

When credentials are missing the client falls back to ``dry-run`` mode:
``send_text_message`` returns a synthetic ``{"dry_run": True, ...}``
payload so the rest of the pipeline (DB, conversation, AI reply) can
be exercised locally without real Meta access.

Dry-run is also force-enabled when the environment variable
``WHATSAPP_DRY_RUN`` is truthy (``1``, ``true``, ``yes``) — useful for
staging environments and integration tests.

We deliberately do not import Meta's official SDK — it is a heavy
dependency and we only need a couple of HTTP calls.
"""
from __future__ import annotations

import logging
import os
from typing import Any
from uuid import uuid4

import httpx

logger = logging.getLogger("ai_sales_agent.whatsapp.cloud_api")


GRAPH_API_BASE = "https://graph.facebook.com"


def _env_flag(name: str) -> bool:
    value = os.environ.get(name)
    if value is None:
        return False
    return value.strip().lower() in ("1", "true", "yes", "on")


class WhatsappCloudAPIError(RuntimeError):
    """Raised when the Cloud API returns a non-2xx response."""

    def __init__(self, *, status_code: int, body: dict[str, Any]) -> None:
        super().__init__(f"WhatsApp Cloud API error {status_code}: {body}")
        self.status_code = status_code
        self.body = body


class WhatsappCloudClient:
    """Async client for the WhatsApp Cloud API.

    The class is stateless across requests; callers are expected to
    obtain a fresh instance per request (or share one for the lifetime
    of the process — both work because we don't keep connections open
    outside of the request scope).
    """

    def __init__(
        self,
        *,
        api_version: str = "v20.0",
        timeout_seconds: float = 15.0,
        http_client: httpx.AsyncClient | None = None,
        force_dry_run: bool | None = None,
    ) -> None:
        self._api_version = api_version
        self._timeout = timeout_seconds
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(timeout=timeout_seconds)
        if force_dry_run is None:
            force_dry_run = _env_flag("WHATSAPP_DRY_RUN")
        self._force_dry_run = force_dry_run

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def send_text_message(
        self,
        *,
        phone_number_id: str,
        access_token: str,
        to_phone: str,
        body: str,
        preview_url: bool = False,
    ) -> dict[str, Any]:
        """Send a text message via the Cloud API.

        Returns the parsed JSON body on success. If ``access_token`` is
        empty, or if ``WHATSAPP_DRY_RUN`` is set, returns a ``dry_run``
        payload so the rest of the system can be exercised without
        real credentials.
        """
        if self._force_dry_run or not access_token:
            return {
                "dry_run": True,
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {"body": body, "preview_url": preview_url},
                "synthetic_id": f"dryrun-{uuid4().hex[:16]}",
            }

        url = f"{GRAPH_API_BASE}/{self._api_version}/{phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"body": body, "preview_url": preview_url},
        }
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = await self._http.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            try:
                err_body: dict[str, Any] = response.json()
            except Exception:  # noqa: BLE001
                err_body = {"raw": response.text}
            logger.warning(
                "Cloud API send failed: status=%s body=%s", response.status_code, err_body
            )
            raise WhatsappCloudAPIError(
                status_code=response.status_code, body=err_body
            )
        try:
            return response.json()
        except Exception:  # noqa: BLE001
            return {"raw": response.text}

    @staticmethod
    def extract_inbound_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Return one dict per ``messages[]`` entry in a webhook payload.

        Meta wraps everything in an ``entry[]`` envelope. We only care
        about ``changes[].value.messages[]`` for now — status updates
        are ignored at this stage and are logged separately.
        """
        results: list[dict[str, Any]] = []
        if not isinstance(payload, dict):
            return results
        for entry in payload.get("entry") or []:
            if not isinstance(entry, dict):
                continue
            for change in entry.get("changes") or []:
                if not isinstance(change, dict):
                    continue
                value = change.get("value") or {}
                if not isinstance(value, dict):
                    continue
                metadata = value.get("metadata") or {}
                phone_number_id = metadata.get("phone_number_id")
                for message in value.get("messages") or []:
                    if not isinstance(message, dict):
                        continue
                    results.append(
                        {
                            "phone_number_id": phone_number_id,
                            "message": message,
                            "contacts": value.get("contacts") or [],
                        }
                    )
        return results


def normalize_phone_for_storage(phone: str) -> str:
    """Return only digits, preserving a leading ``+`` if present."""
    cleaned = "".join(ch for ch in phone.strip() if ch.isdigit() or ch == "+")
    if cleaned.startswith("+"):
        return "+" + "".join(ch for ch in cleaned[1:] if ch.isdigit())
    return "".join(ch for ch in cleaned if ch.isdigit())
