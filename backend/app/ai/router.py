from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.dependencies import get_ai_service
from app.ai.schemas.ai_schemas import (
    ClassifyRequest,
    ClassifyResponse,
    ContextRequest,
    ContextResponse,
    OrchestratorRequest,
    OrchestratorResponse,
)
from app.ai.services.ai_service import AIService
from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission

router = APIRouter()


@router.post("/classify", response_model=ClassifyResponse)
async def classify_message(
    tenant: Annotated[TenantContext, Depends(require_permission("ai:classify"))],
    payload: ClassifyRequest,
    service: Annotated[AIService, Depends(get_ai_service)],
) -> ClassifyResponse:
    return await service.classify(payload)


@router.post("/context", response_model=ContextResponse)
async def build_context(
    tenant: Annotated[TenantContext, Depends(require_permission("ai:context"))],
    payload: ContextRequest,
    service: Annotated[AIService, Depends(get_ai_service)],
) -> ContextResponse:
    return await service.build_context(payload)


@router.post("/respond", response_model=OrchestratorResponse)
async def orchestrate_response(
    tenant: Annotated[TenantContext, Depends(require_permission("ai:respond"))],
    payload: OrchestratorRequest,
    service: Annotated[AIService, Depends(get_ai_service)],
) -> OrchestratorResponse:
    return await service.respond(payload)
