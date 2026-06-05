"""EXECUTIVE DASHBOARD ENTERPRISE V1.

Pure-aggregation module that composes a 360° business view from the
existing tables (``clientes``, ``orders``, ``order_items``,
``sales_pipeline_items``, ``inventory_items``, ``inventory_movements``,
``productos``, ``conversations``, ``conversations_core``,
``whatsapp_messages``). No mutations — read-only.

The module is **strictly additive**: it does not modify any other
module, schema, or router.
"""
from app.modules.executive_dashboard.router import router
from app.modules.executive_dashboard.service import ExecutiveDashboardService
from app.modules.executive_dashboard.repository import ExecutiveDashboardRepository

__all__ = [
    "router",
    "ExecutiveDashboardService",
    "ExecutiveDashboardRepository",
]


def __getattr__(name: str):  # pragma: no cover - re-export shim
    if name == "router":
        from app.modules.executive_dashboard.router import router

        return router
    if name == "ExecutiveDashboardService":
        from app.modules.executive_dashboard.service import ExecutiveDashboardService

        return ExecutiveDashboardService
    if name == "ExecutiveDashboardRepository":
        from app.modules.executive_dashboard.repository import ExecutiveDashboardRepository

        return ExecutiveDashboardRepository
    raise AttributeError(name)
