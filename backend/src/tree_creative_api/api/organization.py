from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from tree_creative_api.api.dependencies import (
    get_application_settings,
    get_authentication_service,
)
from tree_creative_api.api.session import require_session_id
from tree_creative_api.core.config import Settings
from tree_creative_api.modules.auth.schemas import (
    OrganizationMembersResponse,
    OrganizationTreeResponse,
)
from tree_creative_api.modules.auth.service import AuthenticationService

router = APIRouter(prefix="/organization", tags=["organization"])


@router.get("/tree", response_model=OrganizationTreeResponse)
async def organization_tree(
    request: Request,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
    settings: Annotated[Settings, Depends(get_application_settings)],
) -> OrganizationTreeResponse:
    return await service.organization_tree(require_session_id(request, settings))


@router.get("/members", response_model=OrganizationMembersResponse)
async def organization_members(
    request: Request,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
    settings: Annotated[Settings, Depends(get_application_settings)],
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(min_length=1, max_length=4096)] = None,
    department_id: Annotated[
        str | None, Query(alias="departmentId", min_length=1, max_length=128)
    ] = None,
    include_subdepartments: Annotated[bool, Query(alias="includeSubdepartments")] = True,
) -> OrganizationMembersResponse:
    return await service.list_members(
        require_session_id(request, settings),
        page_size=page_size,
        cursor=cursor,
        department_id=department_id,
        include_subdepartments=include_subdepartments,
    )


@router.get("/members/search", response_model=OrganizationMembersResponse)
async def search_organization_members(
    request: Request,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
    settings: Annotated[Settings, Depends(get_application_settings)],
    keyword: Annotated[str, Query(min_length=1, max_length=128)],
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(min_length=1, max_length=4096)] = None,
    department_id: Annotated[
        str | None, Query(alias="departmentId", min_length=1, max_length=128)
    ] = None,
    include_subdepartments: Annotated[bool, Query(alias="includeSubdepartments")] = True,
) -> OrganizationMembersResponse:
    return await service.search_members(
        require_session_id(request, settings),
        keyword=keyword,
        page_size=page_size,
        cursor=cursor,
        department_id=department_id,
        include_subdepartments=include_subdepartments,
    )
