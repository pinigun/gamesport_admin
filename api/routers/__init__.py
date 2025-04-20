from fastapi import APIRouter
from .admins.routes import router as admin_router
from .auth.routes import router as auth_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(admin_router)