from api.chats import router as chats_router
from api.settings import router as settings_router
from api.moderation import router as moderation_router
from api.triggers import router as triggers_router
from api.analytics import router as analytics_router
from api.logs import router as logs_router
from api.admin import router as admin_router

__all__ = [
    "chats_router",
    "settings_router",
    "moderation_router",
    "triggers_router",
    "analytics_router",
    "logs_router",
    "admin_router",
]
