def import_all_models() -> None:
    from app.ai.memory import models as ai_memory_models  # noqa: F401
    from app.ai_live import models as ai_live_models  # noqa: F401
    from app.conversations import models as conversations_core_models  # noqa: F401
    from app.modules.admin import models as admin_models  # noqa: F401
    from app.modules.analytics import models as analytics_models  # noqa: F401
    from app.modules.auth import models as auth_models  # noqa: F401
    from app.modules.chats import models as chats_models  # noqa: F401
    from app.modules.companies import models as companies_models  # noqa: F401
    from app.modules.conversations import models as conversations_models  # noqa: F401
    from app.modules.customers import models as customers_models  # noqa: F401
    from app.modules.orders import models as orders_models  # noqa: F401
    from app.modules.products import models as products_models  # noqa: F401
