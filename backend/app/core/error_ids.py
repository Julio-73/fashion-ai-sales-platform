"""
Enterprise Error ID system.

Generates unique, traceable error identifiers in format:
  ERROR-{YEAR}-{SEQUENTIAL_ID}

Each error is logged with:
  - Unique error ID
  - Timestamp
  - User ID (if available)
  - Tenant ID (if available)
  - Request endpoint
  - Error details

Usage:
  from app.core.error_ids import generate_error_id, log_error
  error_id = generate_error_id()
  log_error(error_id, request=req, error=exc, user_id=user.id)
"""

import datetime
import threading
import logging
from collections.abc import Mapping
from typing import Any

logger = logging.getLogger("ai_sales_agent.errors")

_counter = 0
_counter_lock = threading.Lock()
_error_store: dict[str, dict[str, Any]] = {}


def generate_error_id() -> str:
    global _counter
    year = datetime.datetime.now(datetime.timezone.utc).year
    with _counter_lock:
        _counter += 1
        seq = _counter
    return f"ERROR-{year}-{seq:05d}"


def log_error(
    error_id: str,
    request: Any | None = None,
    error: Exception | None = None,
    user_id: str | None = None,
    tenant_id: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc)

    entry: dict[str, Any] = {
        "error_id": error_id,
        "timestamp": now.isoformat(),
        "user_id": user_id,
        "tenant_id": tenant_id,
        "error_class": error.__class__.__name__ if error else None,
        "error_message": str(error) if error else None,
    }

    if request is not None:
        entry["endpoint"] = getattr(request, "url", {}).get("path") if isinstance(getattr(request, "url", None), Mapping) else str(getattr(request, "url", ""))
        entry["method"] = getattr(request, "method", None)
        if hasattr(request, "headers"):
            entry["request_id"] = request.headers.get("x-request-id")

    if extra:
        entry["extra"] = dict(extra)

    _error_store[error_id] = entry

    log_data = dict(entry)
    log_data["error"] = entry["error_message"]
    logger.error(
        "[%s] %s | user=%s tenant=%s endpoint=%s%s",
        error_id,
        entry["error_class"] or "Error",
        user_id or "-",
        tenant_id or "-",
        entry.get("endpoint") or "-",
        f" | {entry['error_message']}" if entry["error_message"] else "",
        extra={"error_id": error_id, "request_id": entry.get("request_id")},
    )

    return entry


def get_error(error_id: str) -> dict[str, Any] | None:
    return _error_store.get(error_id)


def get_recent_errors(limit: int = 50) -> list[dict[str, Any]]:
    sorted_entries = sorted(_error_store.values(), key=lambda e: e["timestamp"], reverse=True)
    return sorted_entries[:limit]
