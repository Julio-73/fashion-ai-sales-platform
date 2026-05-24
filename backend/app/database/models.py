def import_all_models() -> None:
    from app.modules.analytics import models as analytics_models  # noqa: F401
    from app.modules.auth import models as auth_models  # noqa: F401
    from app.modules.chats import models as chats_models  # noqa: F401
    from app.modules.companies import models as companies_models  # noqa: F401
    from app.modules.conversations import models as conversations_models  # noqa: F401
    from app.modules.customers import models as customers_models  # noqa: F401
    from app.modules.products import models as products_models  # noqa: F401

