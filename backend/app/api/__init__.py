from fastapi import APIRouter

from . import vacations, solve, analytics, config as config_routes

router = APIRouter()

router.include_router(vacations.router, prefix="/vacations", tags=["vacations"])
router.include_router(config_routes.router, prefix="/config", tags=["config"])
router.include_router(solve.router, prefix="/solve", tags=["solve"])
router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])