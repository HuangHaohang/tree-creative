from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from tree_creative_api.modules.auth.schemas import (
    GatewayDepartmentTree,
    GatewayMembersResult,
    GatewayTokenRefresh,
    GatewayTokenVerification,
    GatewayUser,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


class WpsGatewayError(RuntimeError):
    pass


class WpsTokenInvalidError(WpsGatewayError):
    pass


class WpsGatewayUnavailableError(WpsGatewayError):
    pass


class WpsGatewayProtocolError(WpsGatewayError):
    pass


class WpsGatewayHttpClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        client_service: str,
        client_secret: str,
    ) -> None:
        self._http_client = http_client
        self._client_service = client_service
        self._client_secret = client_secret

    async def get_current_user(self, token_envelope: str) -> GatewayUser:
        data = await self._post("/wps/api/org/me", token_envelope)
        return self._validate(GatewayUser, data.get("user"))

    async def verify_token(self, token_envelope: str) -> GatewayTokenVerification:
        data = await self._post("/wps/token/verify", token_envelope)
        return self._validate(GatewayTokenVerification, data)

    async def refresh_token(self, token_envelope: str) -> GatewayTokenRefresh:
        data = await self._post("/wps/token/refresh", token_envelope)
        return self._validate(GatewayTokenRefresh, data)

    async def get_department_tree(self, token_envelope: str) -> GatewayDepartmentTree:
        data = await self._post(
            "/wps/api/org/departments/tree",
            token_envelope,
            includeUsers=True,
            statuses=["active", "notactive", "disabled"],
            contactVisibility="masked",
        )
        return self._validate(GatewayDepartmentTree, data)

    async def list_members(
        self,
        token_envelope: str,
        *,
        page_size: int,
        cursor: str | None,
        department_id: str | None,
        include_subdepartments: bool,
    ) -> GatewayMembersResult:
        return await self._members_request(
            "/wps/api/org/members",
            token_envelope,
            pageSize=page_size,
            cursor=cursor,
            departmentId=department_id,
            includeSubdepartments=include_subdepartments,
            statuses=["active", "notactive", "disabled"],
        )

    async def search_members(
        self,
        token_envelope: str,
        *,
        keyword: str,
        page_size: int,
        cursor: str | None,
        department_id: str | None,
        include_subdepartments: bool,
    ) -> GatewayMembersResult:
        return await self._members_request(
            "/wps/api/org/members/search",
            token_envelope,
            keyword=keyword,
            pageSize=page_size,
            cursor=cursor,
            departmentId=department_id,
            includeSubdepartments=include_subdepartments,
            activeOnly=True,
        )

    async def _members_request(
        self,
        path: str,
        token_envelope: str,
        **payload: object,
    ) -> GatewayMembersResult:
        data = await self._post(path, token_envelope, **payload)
        return self._validate(GatewayMembersResult, data)

    async def _post(
        self,
        path: str,
        token_envelope: str,
        **payload: object,
    ) -> dict[str, Any]:
        request_payload = {
            "clientService": self._client_service,
            "clientSecret": self._client_secret,
            "tokenEnvelope": token_envelope,
            **{key: value for key, value in payload.items() if value is not None},
        }
        try:
            response = await self._http_client.post(path, json=request_payload)
        except httpx.HTTPError as error:
            raise WpsGatewayUnavailableError("WPS gateway request failed") from error

        response_payload = self._read_payload(response)
        if response.is_success:
            data = response_payload.get("data")
            if not isinstance(data, dict):
                raise WpsGatewayProtocolError("WPS gateway response is missing data")
            return data

        error_payload = response_payload.get("error")
        error_code = error_payload.get("code") if isinstance(error_payload, dict) else None
        if response.status_code == 401 and error_code == "AUTH_TOKEN_INVALID":
            raise WpsTokenInvalidError("WPS authorization is no longer valid")
        if response.status_code >= 500:
            raise WpsGatewayUnavailableError("WPS gateway is temporarily unavailable")
        raise WpsGatewayProtocolError(f"WPS gateway rejected request with code {error_code!s}")

    @staticmethod
    def _read_payload(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as error:
            raise WpsGatewayProtocolError("WPS gateway returned invalid JSON") from error
        if not isinstance(payload, dict):
            raise WpsGatewayProtocolError("WPS gateway returned an invalid payload")
        return payload

    @staticmethod
    def _validate(model: type[ModelT], payload: object) -> ModelT:
        try:
            return model.model_validate(payload)
        except ValidationError as error:
            raise WpsGatewayProtocolError("WPS gateway returned an unexpected schema") from error
