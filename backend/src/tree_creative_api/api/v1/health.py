from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from tree_creative_api import __version__
from tree_creative_api.api.dependencies import get_readiness_service
from tree_creative_api.api.schemas import HealthResponse
from tree_creative_api.core.config import get_settings
from tree_creative_api.modules.health.service import ReadinessService

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        service=settings.app_name,
        version=__version__,
        status="ok",
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def readiness(
    response: Response,
    service: Annotated[ReadinessService, Depends(get_readiness_service)],
) -> HealthResponse:
    settings = get_settings()
    snapshot = await service.check()
    if snapshot.status != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse(
        service=settings.app_name,
        version=__version__,
        status=snapshot.status,
        dependencies=snapshot.dependencies,
    )
