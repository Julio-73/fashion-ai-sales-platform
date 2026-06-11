import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.log_formatters import request_id_var
from app.core.redis import get_redis


RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 100

_login_attempts: dict[str, list[float]] = {}
_admin_login_attempts: dict[str, list[float]] = {}


def _is_rate_limited(
    ip: str,
    store: dict[str, list[float]],
    max_requests: int = 10,
    window: int = 60,
) -> bool:
    now = time.time()
    if ip in store:
        store[ip] = [t for t in store[ip] if now - t < window]
        if len(store[ip]) >= max_requests:
            return True
        store[ip].append(now)
    else:
        store[ip] = [now]
    return False


async def _redis_check_rate_limit(key: str, max_requests: int, window: int) -> bool:
    r = await get_redis()
    if r is None:
        return False
    try:
        pipe = r.pipeline()
        now = time.time()
        window_start = now - window
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zcard(key)
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        _, count, _, _ = await pipe.execute()
        return int(count) >= max_requests
    except Exception:
        return False


def register_middleware(app: FastAPI) -> None:
    settings = get_settings()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-Id",
            "Accept",
            "Origin",
        ],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))
        token = request_id_var.set(request_id)
        response = await call_next(request)
        request_id_var.reset(token)
        response.headers["x-request-id"] = request_id
        response.headers["x-content-type-options"] = "nosniff"
        response.headers["x-frame-options"] = "DENY"
        response.headers["content-security-policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'"
        )
        response.headers["strict-transport-security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
        response.headers["permissions-policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
        path = request.url.path

        limited = False
        if path.endswith("/auth/login") or path.endswith("/auth/register"):
            limited = await _redis_check_rate_limit(f"rl:{client_ip}:auth", 10, 60)
            if not limited:
                limited = _is_rate_limited(client_ip, _login_attempts, max_requests=10, window=60)
        elif path.endswith("/admin/auth/login"):
            limited = await _redis_check_rate_limit(f"rl:{client_ip}:admin", 5, 60)
            if not limited:
                limited = _is_rate_limited(client_ip, _admin_login_attempts, max_requests=5, window=60)
        else:
            limited = await _redis_check_rate_limit(f"rl:{client_ip}:global", RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW)
            if not limited:
                limited = _is_rate_limited(client_ip, _login_attempts, max_requests=RATE_LIMIT_MAX_REQUESTS, window=RATE_LIMIT_WINDOW)

        if limited:
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "rate_limit_exceeded", "message": "Too many requests. Try again later."}},
            )

        return await call_next(request)
