"""
Production configuration for AI Sales Agent SaaS.

Overrides default settings when APP_ENV=production.
Imported by app.core.config and applied during application startup.
"""

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "app.core.log_formatters.JSONFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "logs/error.log",
            "maxBytes": 50 * 1024 * 1024,
            "backupCount": 10,
            "encoding": "utf-8",
            "level": "ERROR",
        },
        "api_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "json",
            "filename": "logs/api.log",
            "maxBytes": 50 * 1024 * 1024,
            "backupCount": 10,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "ai_sales_agent": {"handlers": ["console", "api_file"], "level": "INFO", "propagate": False},
        "ai_sales_agent.errors": {"handlers": ["error_file"], "level": "ERROR", "propagate": False},
        "uvicorn.access": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "sqlalchemy.engine": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

WORKERS = 4

DATABASE_POOL = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 1800,
}

CORS = {
    "allow_credentials": True,
    "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": ["Authorization", "Content-Type", "X-Request-Id", "Accept", "Origin"],
}

SECURITY = {
    "content_security_policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'",
    "strict_transport_security": "max-age=31536000; includeSubDomains",
    "referrer_policy": "strict-origin-when-cross-origin",
    "permissions_policy": "camera=(), microphone=(), geolocation=()",
}

CACHE = {
    "default_timeout": 300,
    "key_prefix": "aisales:",
}

TIMEOUTS = {
    "openai_request": 30,
    "database_query": 30,
    "whatsapp_request": 15,
}
