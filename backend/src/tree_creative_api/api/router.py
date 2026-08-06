from fastapi import APIRouter

from tree_creative_api.api.auth import auth_router, oauth_router
from tree_creative_api.api.organization import router as organization_router
from tree_creative_api.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)

integration_router = APIRouter(prefix="/api")
integration_router.include_router(auth_router)
integration_router.include_router(oauth_router)
integration_router.include_router(organization_router)
