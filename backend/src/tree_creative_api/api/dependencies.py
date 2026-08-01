from typing import cast

from fastapi import Request

from tree_creative_api.modules.health.service import ReadinessService


def get_readiness_service(request: Request) -> ReadinessService:
    return cast(ReadinessService, request.app.state.readiness_service)
