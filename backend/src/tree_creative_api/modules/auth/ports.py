from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from tree_creative_api.modules.auth.domain import (
    AuthenticatedUser,
    ExternalIdentity,
    LoginTransaction,
)
from tree_creative_api.modules.auth.schemas import (
    GatewayDepartmentTree,
    GatewayMembersResult,
    GatewayTokenRefresh,
    GatewayTokenVerification,
    GatewayUser,
    ServerSession,
)


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


class LoginTransactionStore(Protocol):
    async def create(self, state: str, transaction: LoginTransaction, ttl_seconds: int) -> None: ...

    async def consume(self, state: str) -> LoginTransaction | None: ...


class SessionStore(Protocol):
    async def create(self, session: ServerSession, ttl_seconds: int) -> None: ...

    async def get(self, session_id: str) -> ServerSession | None: ...

    async def replace(self, session: ServerSession) -> bool: ...

    async def revoke(self, session_id: str) -> None: ...


class UserRepository(Protocol):
    async def upsert_wps_user(
        self, user: GatewayUser, wps_company_id: str
    ) -> AuthenticatedUser: ...


class AuditRepository(Protocol):
    async def record(
        self,
        event_type: str,
        *,
        user_id: str | None,
        provider: str,
        occurred_at: datetime,
        details: dict[str, object] | None = None,
    ) -> None: ...


class WpsGateway(Protocol):
    async def get_current_user(self, token_envelope: str) -> GatewayUser: ...

    async def verify_token(self, token_envelope: str) -> GatewayTokenVerification: ...

    async def refresh_token(self, token_envelope: str) -> GatewayTokenRefresh: ...

    async def get_department_tree(self, token_envelope: str) -> GatewayDepartmentTree: ...

    async def list_members(
        self,
        token_envelope: str,
        *,
        page_size: int,
        cursor: str | None,
        department_id: str | None,
        include_subdepartments: bool,
    ) -> GatewayMembersResult: ...

    async def search_members(
        self,
        token_envelope: str,
        *,
        keyword: str,
        page_size: int,
        cursor: str | None,
        department_id: str | None,
        include_subdepartments: bool,
    ) -> GatewayMembersResult: ...
