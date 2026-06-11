import logging
import logging.handlers
import os
import sys
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
API_LOG_FILE = LOG_DIR / "api.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"
AUTOMATION_LOG_FILE = LOG_DIR / "automation.log"


def _make_json_formatter() -> logging.Formatter:
    from app.core.log_formatters import JSONFormatter
    return JSONFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z")


def _make_text_formatter() -> logging.Formatter:
    return logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    is_production = os.environ.get("APP_ENV", "local") == "production"
    formatter = _make_json_formatter() if is_production else _make_text_formatter()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    api_handler = logging.handlers.RotatingFileHandler(
        API_LOG_FILE, maxBytes=50 * 1024 * 1024 if is_production else 10 * 1024 * 1024,
        backupCount=10 if is_production else 5, encoding="utf-8"
    )
    api_handler.setFormatter(formatter)
    api_handler.setLevel(logging.INFO)
    api_handler.addFilter(lambda record: "automation" not in record.name)
    root_logger.addHandler(api_handler)

    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE, maxBytes=50 * 1024 * 1024 if is_production else 10 * 1024 * 1024,
        backupCount=10 if is_production else 5, encoding="utf-8"
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    automation_handler = logging.handlers.RotatingFileHandler(
        AUTOMATION_LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    automation_handler.setFormatter(formatter)
    automation_handler.setLevel(logging.INFO)
    root_logger.addHandler(automation_handler)

    if is_production:
        root_logger.info("Production logging active — JSON format, 50MB rotated logs")

    logging.getLogger("ai_sales_agent").setLevel(logging.INFO)
    logging.getLogger("ai_sales_agent.database").setLevel(logging.INFO)
    logging.getLogger("ai_sales_agent.admin").setLevel(logging.INFO)
    logging.getLogger("ai_sales_agent.automation").setLevel(logging.INFO)
    logging.getLogger("ai_sales_agent.auth").setLevel(logging.INFO)
    logging.getLogger("ai_sales_agent.whatsapp").setLevel(logging.INFO)
    logging.getLogger("ai_sales_agent.errors").setLevel(logging.WARNING)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
