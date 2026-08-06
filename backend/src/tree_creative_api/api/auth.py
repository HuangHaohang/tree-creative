from typing import Annotated
from urllib.parse import urljoin, urlsplit

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from tree_creative_api.api.dependencies import (
    get_application_settings,
    get_authentication_service,
)
from tree_creative_api.api.session import require_session_id, session_id
from tree_creative_api.core.config import Settings
from tree_creative_api.core.errors import ApiError
from tree_creative_api.modules.auth.schemas import CurrentUserResponse, WpsCallbackPayload
from tree_creative_api.modules.auth.service import AuthenticationService

auth_router = APIRouter(prefix="/auth", tags=["authentication"])
oauth_router = APIRouter(prefix="/oauth", tags=["authentication"])


def _safe_return_path(value: str) -> str:
    if (
        not value.startswith("/")
        or value.startswith("//")
        or "\\" in value
        or any(ord(character) < 32 for character in value)
    ):
        return "/home"
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.path == "/login":
        return "/home"
    return value


def _clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        settings.auth_session_cookie_name,
        path="/",
        secure=settings.auth_session_cookie_secure,
        httponly=True,
        samesite="lax",
    )


@auth_router.get("/wps/login", response_class=RedirectResponse)
async def begin_wps_login(
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
    return_to: Annotated[str, Query(alias="returnTo", max_length=2048)] = "/home",
) -> RedirectResponse:
    response = RedirectResponse(
        await service.begin_wps_login(_safe_return_path(return_to)),
        status_code=302,
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@oauth_router.post("/callback", response_class=RedirectResponse)
async def complete_wps_login(
    request: Request,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
    settings: Annotated[Settings, Depends(get_application_settings)],
) -> RedirectResponse:
    form = await request.form()
    try:
        callback = WpsCallbackPayload.model_validate(dict(form))
    except ValidationError as error:
        raise ApiError(
            code="invalid_oauth_callback",
            message="WPS callback payload is invalid",
            status_code=400,
        ) from error
    completed = await service.complete_wps_login(callback)
    session = completed.session
    response = RedirectResponse(
        urljoin(service.frontend_url, completed.return_path.lstrip("/")),
        status_code=302,
    )
    response.set_cookie(
        settings.auth_session_cookie_name,
        session.id,
        max_age=settings.auth_session_ttl_seconds,
        path="/",
        secure=settings.auth_session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@auth_router.get("/me", response_model=CurrentUserResponse)
async def current_user(
    request: Request,
    response: Response,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
    settings: Annotated[Settings, Depends(get_application_settings)],
) -> CurrentUserResponse:
    response.headers["Cache-Control"] = "no-store"
    return await service.current_user(require_session_id(request, settings))


@auth_router.post("/logout", status_code=204)
async def logout(
    request: Request,
    service: Annotated[AuthenticationService, Depends(get_authentication_service)],
    settings: Annotated[Settings, Depends(get_application_settings)],
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    await service.logout(session_id(request, settings), csrf_token)
    response = Response(status_code=204)
    _clear_session_cookie(response, settings)
    response.headers["Cache-Control"] = "no-store"
    return response
