"""Fernet encryption helpers for sensitive fields (e.g. WhatsApp tokens).

Gracefully degrades: if no encryption key is configured, data is stored
in plaintext (backwards-compatible for local development).
"""
from __future__ import annotations

import base64
import hashlib
import logging

from app.core.config import get_settings

logger = logging.getLogger("ai_sales_agent.encryption")

_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is not None:
        return _fernet
    settings = get_settings()
    raw_key = settings.whatsapp_encryption_key
    if not raw_key:
        logger.warning("WHATSAPP_ENCRYPTION_KEY not set — tokens stored in plaintext")
        return None
    try:
        from cryptography.fernet import Fernet

        # Derive a 32-byte URL-safe base64 key from any string
        key = base64.urlsafe_b64encode(hashlib.sha256(raw_key.encode()).digest())
        _fernet = Fernet(key)
        return _fernet
    except Exception:
        logger.exception("Failed to initialize Fernet encryption")
        return None


def encrypt(plaintext: str) -> str:
    f = _get_fernet()
    if f is None:
        return plaintext
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    f = _get_fernet()
    if f is None:
        return ciphertext
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        logger.exception("Decryption failed — returning raw value")
        return ciphertext
