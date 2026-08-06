from fastapi import Request

from tree_creative_api.core.config import Settings
from tree_creative_api.core.errors import ApiError


def session_id(request: Request, settings: Settings) -> str | None:
    return request.cookies.get(settings.auth_session_cookie_name)


def require_session_id(request: Request, settings: Settings) -> str:
    value = session_id(request, settings)
    if value is None:
        raise ApiError(
            code="authentication_required",
            message="Authentication is required",
            status_code=401,
        )
    return value
