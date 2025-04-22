from fastapi import APIRouter

from .auth.routes import router as auth_router
from .users.routes import router as users_router
from .admins.routes import router as admin_router
from .faq.routes import router as faq_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(users_router)
api_router.include_router(faq_router)