from handlers.system import router as system_router
from handlers.common import router as common_router
from handlers.admin import router as admin_router

__all__ = ["system_router", "common_router", "admin_router"]
