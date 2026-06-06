from fastapi import APIRouter

from app.ai.router import router as ai_router
from app.ai_live.router import router as ai_live_router
from app.api.routes.health import router as health_router
from app.conversations.router import router as conversations_core_router
from app.modules.admin.router import router as admin_router
from app.modules.analytics.router import router as analytics_router
from app.modules.auth.router import router as auth_router
from app.modules.chats.router import router as chats_router
from app.modules.conversations.router import router as conversations_router
from app.modules.companies.router import router as companies_router
from app.modules.crm.router import router as crm_router
from app.modules.customers.router import router as customers_router
from app.modules.executive_dashboard.router import router as executive_dashboard_router
from app.modules.inventory.router import router as inventory_router
from app.modules.orders.router import router as orders_router
from app.modules.pipeline.router import router as pipeline_router
from app.modules.products.router import router as products_router
from app.modules.reporting.router import router as reporting_router
from app.modules.whatsapp.router import router as whatsapp_router
from app.sales.api.router import router as sales_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(companies_router, prefix="/companies", tags=["companies"])
api_router.include_router(customers_router, prefix="/customers", tags=["customers"])
api_router.include_router(crm_router, prefix="/crm", tags=["crm"])
api_router.include_router(executive_dashboard_router, prefix="/executive-dashboard", tags=["executive-dashboard"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["inventory"])
api_router.include_router(products_router, prefix="/products", tags=["products"])
api_router.include_router(orders_router, prefix="/orders", tags=["orders"])
api_router.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])
api_router.include_router(reporting_router, prefix="/reporting", tags=["reporting"])
api_router.include_router(chats_router, prefix="/chats", tags=["chats"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["conversations"])
api_router.include_router(conversations_core_router, prefix="/conversations-core", tags=["conversations-core"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(sales_router, prefix="/sales", tags=["sales"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(ai_live_router, prefix="/ai-live", tags=["ai-live"])
api_router.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])
