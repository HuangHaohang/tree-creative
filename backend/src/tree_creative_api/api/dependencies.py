from typing import cast

from fastapi import Request

from tree_creative_api.core.config import Settings
from tree_creative_api.infrastructure.resources import ApplicationResources
from tree_creative_api.modules.auth.service import AuthenticationService
from tree_creative_api.modules.health.service import ReadinessService


def get_readiness_service(request: Request) -> ReadinessService:
    return cast(ReadinessService, request.app.state.readiness_service)


def get_application_resources(request: Request) -> ApplicationResources:
    return cast(ApplicationResources, request.app.state.resources)


def get_authentication_service(request: Request) -> AuthenticationService:
    return get_application_resources(request).auth_service


def get_application_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)
