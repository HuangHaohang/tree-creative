import json

import httpx
import pytest

from tree_creative_api.infrastructure.wps_gateway import (
    WpsGatewayHttpClient,
    WpsGatewayUnavailableError,
    WpsTokenInvalidError,
)


@pytest.mark.asyncio
async def test_department_tree_uses_server_credentials_and_masked_contacts() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "data": {
                    "tree": {
                        "id": "root",
                        "name": "公司",
                        "children": [],
                        "users": [],
                    },
                    "users": {"total": 0, "attached": 0, "unassigned": []},
                }
            },
        )

    async with httpx.AsyncClient(
        base_url="https://gateway.example.test",
        transport=httpx.MockTransport(handler),
    ) as http_client:
        gateway = WpsGatewayHttpClient(
            http_client,
            client_service="tree-creative",
            client_secret="test-only-placeholder",
        )
        result = await gateway.get_department_tree("test-envelope")

    assert result.tree.id == "root"
    assert captured == {
        "clientService": "tree-creative",
        "clientSecret": "test-only-placeholder",
        "tokenEnvelope": "test-envelope",
        "includeUsers": True,
        "statuses": ["active", "notactive", "disabled"],
        "contactVisibility": "masked",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "code", "error_type"),
    [
        (401, "AUTH_TOKEN_INVALID", WpsTokenInvalidError),
        (502, "PROVIDER_NETWORK_ERROR", WpsGatewayUnavailableError),
    ],
)
async def test_gateway_distinguishes_invalid_tokens_from_temporary_failures(
    status: int,
    code: str,
    error_type: type[Exception],
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": {"code": code, "message": "failed"}})

    async with httpx.AsyncClient(
        base_url="https://gateway.example.test",
        transport=httpx.MockTransport(handler),
    ) as http_client:
        gateway = WpsGatewayHttpClient(
            http_client,
            client_service="tree-creative",
            client_secret="test-only-placeholder",
        )
        with pytest.raises(error_type):
            await gateway.verify_token("test-envelope")
