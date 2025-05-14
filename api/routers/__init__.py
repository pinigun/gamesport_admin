from fastapi import APIRouter

from .faq.routes import router as faq_router
from .auth.routes import router as auth_router
from .users.routes import router as users_router
from .tasks.routes import router as tasks_router
from .admins.routes import router as admin_router
from .giveaways.routes import router as giveaways_router
from .statistics.routes import router as statistics_router
from .dashboards.routes import router as dashboards_router
from .campaign.routes import router as campaign_router
from .docs.routes import router as docs_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(users_router)
api_router.include_router(statistics_router)
api_router.include_router(dashboards_router)
api_router.include_router(giveaways_router)
api_router.include_router(tasks_router)
api_router.include_router(faq_router)
api_router.include_router(campaign_router)
api_router.include_router(docs_router)