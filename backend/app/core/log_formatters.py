"""
JSON log formatter for production structured logging.

Outputs logs as newline-delimited JSON for ingestion by
Logstash, Datadog, Splunk, or any JSON log aggregator.
"""

import json
import logging
from contextvars import ContextVar
from typing import override

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JSONFormatter(logging.Formatter):
    def __init__(self, fmt: str | None = None, datefmt: str | None = None, style: str = "%") -> None:
        super().__init__(fmt, datefmt, style)
        self._field_order = fmt.split() if fmt else None

    @override
    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, object] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id
        if hasattr(record, "error_id"):
            log_entry["error_id"] = record.error_id
        if hasattr(record, "tenant_id"):
            log_entry["tenant_id"] = record.tenant_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False, default=str)
