from backend.routers.auth_router import router as auth_router
from backend.routers.users_router import router as users_router
from backend.routers.admin_router import router as admin_router

__all__ = ["auth_router", "users_router", "admin_router"]
