from dataclasses import dataclass

import pytest

from tree_creative_api.modules.auth.authorization import AuthorizationService
from tree_creative_api.modules.auth.domain import ExternalIdentity, Principal
from tree_creative_api.modules.auth.ports import LoginCallback, LoginRedirect, LoginRequest
from tree_creative_api.modules.auth.registry import (
    DuplicateIdentityProviderError,
    IdentityProviderRegistry,
    UnknownIdentityProviderError,
)


@dataclass
class StubProvider:
    name: str

    async def begin_login(self, request: LoginRequest) -> LoginRedirect:
        return LoginRedirect(url=request.redirect_url)

    async def authenticate(self, callback: LoginCallback) -> ExternalIdentity:
        return ExternalIdentity(provider=self.name, subject=callback.code)

    async def logout_url(self, post_logout_redirect_url: str) -> str | None:
        return post_logout_redirect_url


def test_identity_provider_registry_is_extensible() -> None:
    provider = StubProvider(name="oidc")
    registry = IdentityProviderRegistry([provider])

    assert registry.names() == ("oidc",)
    assert registry.get("oidc") is provider


def test_identity_provider_registry_rejects_duplicates_and_unknown_names() -> None:
    registry = IdentityProviderRegistry([StubProvider(name="oidc")])

    with pytest.raises(DuplicateIdentityProviderError):
        registry.register(StubProvider(name="oidc"))
    with pytest.raises(UnknownIdentityProviderError):
        registry.get("saml")


def test_authorization_defaults_to_deny() -> None:
    principal = Principal(
        user_id="user-1",
        display_name="Example",
        permissions=frozenset({"project:read"}),
    )

    assert AuthorizationService.allows(principal, "project:read")
    assert not AuthorizationService.allows(principal, "project:write")
    assert not AuthorizationService.allows(None, "project:read")
