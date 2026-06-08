from fastapi import APIRouter, Depends, Request, status

from app.core.security.dependencies import AuthenticatedUser, get_current_user
from app.modules.auth.dependencies import get_auth_service
from app.modules.auth.schemas import (
    AuthSessionResponse,
    CurrentUserResponse,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


@router.post("/register", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> AuthSessionResponse:
    return await service.register(payload, ip_address=_client_ip(request))


@router.post("/login", response_model=AuthSessionResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> AuthSessionResponse:
    return await service.login(payload, ip_address=_client_ip(request))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await service.refresh(payload)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout(RefreshTokenRequest(refresh_token=payload.refresh_token))


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(
    user: AuthenticatedUser = Depends(get_current_user),
) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(user)
