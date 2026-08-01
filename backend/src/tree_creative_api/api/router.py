from fastapi import APIRouter

from tree_creative_api.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
