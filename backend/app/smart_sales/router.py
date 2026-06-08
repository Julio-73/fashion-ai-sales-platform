"""REST API for the Smart Sales engine.

Thin wrappers that expose existing SmartSalesBrain capabilities as HTTP
endpoints. No internal business logic is duplicated.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.smart_sales.brain import SmartSalesBrain
from app.smart_sales.entity_extractor import EntityExtractor
from app.smart_sales.recommendation_engine import RecommendationEngine
from app.smart_sales.product_context import ProductContextEngine

router = APIRouter()


class AnalyzeRequest(BaseModel):
    empresa_id: str
    message: str


class AnalyzeResponse(BaseModel):
    product_type: str | None
    size: str | None
    color: str | None
    gender: str | None
    style: str | None
    occasion: str | None


class RecommendRequest(BaseModel):
    empresa_id: str
    current_product_type: str | None = None
    current_product_category: str | None = None


class RecommendResponse(BaseModel):
    recommendations: list[dict]


class GenerateRequest(BaseModel):
    empresa_id: str
    message: str
    conversation_id: str | None = None


class GenerateResponse(BaseModel):
    response: str


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(payload: AnalyzeRequest):
    extractor = EntityExtractor()
    entities = extractor.extract(payload.message)
    return AnalyzeResponse(
        product_type=entities.product_type,
        size=entities.size,
        color=entities.color,
        gender=entities.gender,
        style=entities.style,
        occasion=entities.occasion,
    )


@router.post("/recommend", response_model=RecommendResponse)
async def get_recommendations(payload: RecommendRequest, session: AsyncSession = Depends(get_db_session)):
    engine = RecommendationEngine(ProductContextEngine(session))
    recs = await engine.generate_recommendations(
        empresa_id=UUID(payload.empresa_id),
        current_product_type=payload.current_product_type,
        current_product_category=payload.current_product_category,
    )
    return RecommendResponse(
        recommendations=[
            {"category": r.category, "suggestion": r.suggestion, "products_count": r.products_count}
            for r in recs
        ]
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate_reply(payload: GenerateRequest, session: AsyncSession = Depends(get_db_session)):
    brain = SmartSalesBrain(session)
    response = await brain.generate_reply(
        empresa_id=UUID(payload.empresa_id),
        user_message=payload.message,
        conversation_id=UUID(payload.conversation_id) if payload.conversation_id else None,
    )
    return GenerateResponse(response=response)
