"""SALES PIPELINE ENTERPRISE V1.

Pipeline module — materialised sales "deals" moving through a funnel
of stages. Reads from existing modules (customers/crm/conversations/orders/
whatsapp/ai-live) without modifying them.
"""
from app.modules.pipeline.models import (
    CLOSED_STAGES,
    LOST_STAGE,
    NEW_LEAD_STAGE,
    OPEN_STAGES,
    PIPELINE_STAGE_VALUES,
    WON_STAGE,
    SalesPipelineItem,
    is_valid_stage,
)

__all__ = [
    "router",
    "PipelineService",
    "CommercialAI",
    "AutomationEngine",
    "SalesPipelineItem",
    "PIPELINE_STAGE_VALUES",
    "OPEN_STAGES",
    "CLOSED_STAGES",
    "WON_STAGE",
    "LOST_STAGE",
    "NEW_LEAD_STAGE",
    "is_valid_stage",
]


def __getattr__(name: str):  # pragma: no cover - re-export shim
    if name == "router":
        from app.modules.pipeline.router import router
        return router
    if name == "PipelineService":
        from app.modules.pipeline.service import PipelineService
        return PipelineService
    if name == "CommercialAI":
        from app.modules.pipeline.ai import CommercialAI
        return CommercialAI
    if name == "AutomationEngine":
        from app.modules.pipeline.automations import AutomationEngine
        return AutomationEngine
    raise AttributeError(name)
