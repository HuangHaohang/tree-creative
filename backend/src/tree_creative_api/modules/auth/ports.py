from dataclasses import dataclass
from typing import Protocol

from tree_creative_api.modules.auth.domain import ExternalIdentity


@dataclass(frozen=True, slots=True)
class LoginRequest:
    redirect_url: str
    state: str


@dataclass(frozen=True, slots=True)
class LoginRedirect:
    url: str


@dataclass(frozen=True, slots=True)
class LoginCallback:
    code: str
    state: str
    redirect_url: str


class IdentityProvider(Protocol):
    @property
    def name(self) -> str: ...

    async def begin_login(self, request: LoginRequest) -> LoginRedirect: ...

    async def authenticate(self, callback: LoginCallback) -> ExternalIdentity: ...

    async def logout_url(self, post_logout_redirect_url: str) -> str | None: ...
