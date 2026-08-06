import logging
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TypeVar
from urllib.parse import urlencode, urljoin

from tree_creative_api.core.errors import ApiError
from tree_creative_api.infrastructure.wps_gateway import (
    WpsGatewayProtocolError,
    WpsGatewayUnavailableError,
    WpsTokenInvalidError,
)
from tree_creative_api.modules.auth.domain import LoginTransaction
from tree_creative_api.modules.auth.ports import (
    AuditRepository,
    LoginTransactionStore,
    SessionStore,
    UserRepository,
    WpsGateway,
)
from tree_creative_api.modules.auth.schemas import (
    CurrentUser,
    CurrentUserResponse,
    DepartmentNode,
    DirectoryMember,
    DirectoryUser,
    GatewayDepartmentNode,
    GatewayMember,
    GatewayMembersResult,
    GatewayUser,
    MembersPage,
    OrganizationMembersResponse,
    OrganizationTreeResponse,
    ServerSession,
    SessionUser,
    TreeUserStats,
    WpsCallbackPayload,
)

logger = logging.getLogger(__name__)
ResultT = TypeVar("ResultT")


@dataclass(frozen=True, slots=True)
class CompletedLogin:
    session: ServerSession
    return_path: str


class AuthenticationService:
    def __init__(
        self,
        *,
        gateway: WpsGateway,
        login_transactions: LoginTransactionStore,
        sessions: SessionStore,
        users: UserRepository,
        audits: AuditRepository,
        gateway_base_url: str,
        client_service: str,
        redirect_uri: str,
        frontend_base_url: str,
        login_state_ttl_seconds: int,
        session_ttl_seconds: int,
        token_verify_interval_seconds: int,
        token_refresh_leeway_seconds: int,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._gateway = gateway
        self._login_transactions = login_transactions
        self._sessions = sessions
        self._users = users
        self._audits = audits
        self._gateway_base_url = gateway_base_url.rstrip("/") + "/"
        self._client_service = client_service
        self._redirect_uri = redirect_uri
        self._frontend_base_url = frontend_base_url.rstrip("/") + "/"
        self._login_state_ttl_seconds = login_state_ttl_seconds
        self._session_ttl_seconds = session_ttl_seconds
        self._token_verify_interval = timedelta(seconds=token_verify_interval_seconds)
        self._token_refresh_leeway = timedelta(seconds=token_refresh_leeway_seconds)
        self._now = now or (lambda: datetime.now(UTC))

    @property
    def frontend_url(self) -> str:
        return self._frontend_base_url

    async def begin_wps_login(self, return_path: str = "/home") -> str:
        state = secrets.token_urlsafe(32)
        await self._login_transactions.create(
            state,
            LoginTransaction(
                redirect_uri=self._redirect_uri,
                return_path=return_path,
                created_at=self._now(),
            ),
            self._login_state_ttl_seconds,
        )
        query = urlencode(
            {
                "client_service": self._client_service,
                "redirect_uri": self._redirect_uri,
                "state": state,
                "response_mode": "form_post",
            }
        )
        return f"{urljoin(self._gateway_base_url, 'wps/sso/login')}?{query}"

    async def complete_wps_login(self, callback: WpsCallbackPayload) -> CompletedLogin:
        if callback.token_type != "wps_token_envelope":
            raise ApiError(
                code="invalid_token_type",
                message="WPS callback token type is invalid",
                status_code=400,
            )
        transaction = await self._login_transactions.consume(callback.state)
        if transaction is None:
            raise ApiError(
                code="invalid_login_state",
                message="Login state is invalid, expired, or already used",
                status_code=400,
            )

        gateway_user = await self._call_gateway(
            self._gateway.get_current_user(callback.token_envelope)
        )
        if gateway_user.id != callback.wps_user_id:
            raise ApiError(
                code="identity_mismatch",
                message="WPS callback identity does not match the authenticated user",
                status_code=400,
            )

        now = self._now()
        if callback.refresh_expires_at <= now:
            raise ApiError(
                code="expired_callback_token",
                message="WPS callback refresh authorization has expired",
                status_code=400,
            )

        authenticated_user = await self._users.upsert_wps_user(
            gateway_user,
            callback.wps_company_id,
        )
        session = ServerSession(
            id=secrets.token_urlsafe(32),
            csrf_token=secrets.token_urlsafe(32),
            token_envelope=callback.token_envelope,
            access_expires_at=callback.access_expires_at,
            refresh_expires_at=callback.refresh_expires_at,
            verified_at=now,
            created_at=now,
            user=SessionUser(
                id=authenticated_user.id,
                display_name=authenticated_user.display_name,
                avatar_url=authenticated_user.avatar_url,
                organization_name=authenticated_user.organization_name,
                title=authenticated_user.title,
                employee_id=authenticated_user.employee_id,
                status=authenticated_user.status,
                permissions=sorted(authenticated_user.permissions),
                wps_user_id=authenticated_user.wps_user_id,
                wps_company_id=authenticated_user.wps_company_id,
            ),
        )
        ttl_seconds = min(
            self._session_ttl_seconds,
            max(1, int((callback.refresh_expires_at - now).total_seconds())),
        )
        await self._sessions.create(session, ttl_seconds)
        await self._audits.record(
            "auth.login.succeeded",
            user_id=authenticated_user.id,
            provider="wps",
            occurred_at=now,
        )
        return CompletedLogin(session=session, return_path=transaction.return_path)

    async def current_user(self, session_id: str) -> CurrentUserResponse:
        session = await self.require_session(session_id)
        return CurrentUserResponse(
            user=CurrentUser(
                id=session.user.id,
                display_name=session.user.display_name,
                avatar_url=session.user.avatar_url,
                organization_name=session.user.organization_name,
                title=session.user.title,
                employee_id=session.user.employee_id,
                status=session.user.status,
                permissions=session.user.permissions,
            ),
            csrf_token=session.csrf_token,
        )

    async def logout(self, session_id: str | None, csrf_token: str | None) -> None:
        if session_id is None:
            return
        session = await self._sessions.get(session_id)
        if session is None:
            return
        if csrf_token is None or not secrets.compare_digest(csrf_token, session.csrf_token):
            raise ApiError(
                code="csrf_validation_failed",
                message="CSRF token is missing or invalid",
                status_code=403,
            )
        await self._sessions.revoke(session_id)
        try:
            await self._audits.record(
                "auth.logout.succeeded",
                user_id=session.user.id,
                provider="wps",
                occurred_at=self._now(),
            )
        except Exception:
            logger.exception("Failed to persist logout audit event")

    async def organization_tree(self, session_id: str) -> OrganizationTreeResponse:
        session = await self.require_session(session_id)
        result = await self._with_session_gateway_call(
            session,
            self._gateway.get_department_tree,
        )
        return OrganizationTreeResponse(
            tree=self._map_department(result.tree),
            users=TreeUserStats(
                total=result.users.total,
                attached=result.users.attached,
                unassigned=[self._map_directory_user(user) for user in result.users.unassigned],
            ),
        )

    async def list_members(
        self,
        session_id: str,
        *,
        page_size: int,
        cursor: str | None,
        department_id: str | None,
        include_subdepartments: bool,
    ) -> OrganizationMembersResponse:
        session = await self.require_session(session_id)
        result = await self._call_gateway(
            self._gateway.list_members(
                session.token_envelope,
                page_size=page_size,
                cursor=cursor,
                department_id=department_id,
                include_subdepartments=include_subdepartments,
            ),
            session_id=session.id,
        )
        return self._map_members(result)

    async def search_members(
        self,
        session_id: str,
        *,
        keyword: str,
        page_size: int,
        cursor: str | None,
        department_id: str | None,
        include_subdepartments: bool,
    ) -> OrganizationMembersResponse:
        session = await self.require_session(session_id)
        result = await self._call_gateway(
            self._gateway.search_members(
                session.token_envelope,
                keyword=keyword,
                page_size=page_size,
                cursor=cursor,
                department_id=department_id,
                include_subdepartments=include_subdepartments,
            ),
            session_id=session.id,
        )
        return self._map_members(result)

    async def require_session(self, session_id: str) -> ServerSession:
        session = await self._sessions.get(session_id)
        if session is None:
            raise self._unauthorized()
        now = self._now()
        if session.refresh_expires_at <= now:
            await self._sessions.revoke(session_id)
            raise self._unauthorized()
        if session.access_expires_at <= now + self._token_refresh_leeway:
            return await self._refresh_session(session)
        if session.verified_at <= now - self._token_verify_interval:
            verification = await self._call_gateway(
                self._gateway.verify_token(session.token_envelope),
                session_id=session.id,
            )
            if not verification.active:
                await self._sessions.revoke(session.id)
                raise self._unauthorized()
            verified_session = session.model_copy(update={"verified_at": now})
            if not await self._sessions.replace(verified_session):
                raise self._unauthorized()
            return verified_session
        return session

    async def _refresh_session(self, session: ServerSession) -> ServerSession:
        refreshed = await self._call_gateway(
            self._gateway.refresh_token(session.token_envelope),
            session_id=session.id,
        )
        if refreshed.token_type != "wps_token_envelope":
            raise ApiError(
                code="gateway_protocol_error",
                message="WPS gateway returned an invalid token type",
                status_code=502,
            )
        updated = session.model_copy(
            update={
                "token_envelope": refreshed.token_envelope,
                "access_expires_at": refreshed.access_expires_at,
                "refresh_expires_at": refreshed.refresh_expires_at,
                "verified_at": self._now(),
            }
        )
        if not await self._sessions.replace(updated):
            raise self._unauthorized()
        return updated

    async def _with_session_gateway_call(
        self,
        session: ServerSession,
        call: Callable[[str], Awaitable[ResultT]],
    ) -> ResultT:
        return await self._call_gateway(call(session.token_envelope), session_id=session.id)

    async def _call_gateway(
        self,
        awaitable: Awaitable[ResultT],
        session_id: str | None = None,
    ) -> ResultT:
        try:
            return await awaitable
        except WpsTokenInvalidError as error:
            if session_id is not None:
                await self._sessions.revoke(session_id)
            raise self._unauthorized() from error
        except WpsGatewayUnavailableError as error:
            raise ApiError(
                code="gateway_unavailable",
                message="WPS gateway is temporarily unavailable",
                status_code=503,
            ) from error
        except WpsGatewayProtocolError as error:
            raise ApiError(
                code="gateway_protocol_error",
                message="WPS gateway returned an invalid response",
                status_code=502,
            ) from error

    @staticmethod
    def _unauthorized() -> ApiError:
        return ApiError(
            code="authentication_required",
            message="Authentication is required",
            status_code=401,
        )

    @classmethod
    def _map_department(cls, node: GatewayDepartmentNode) -> DepartmentNode:
        return DepartmentNode(
            id=node.id,
            name=node.name,
            parent_id=node.parent_id,
            path=node.path,
            enabled=node.enabled,
            children=[cls._map_department(child) for child in node.children],
            users=[cls._map_directory_user(user) for user in node.users],
        )

    @staticmethod
    def _map_directory_user(user: GatewayUser) -> DirectoryUser:
        return DirectoryUser(
            id=user.id,
            display_name=user.display_name,
            avatar_url=user.avatar,
            status=user.status,
            title=user.title,
            employee_id=user.employee_id,
            primary_department=user.primary_department,
            departments=user.departments,
            contacts=user.contacts,
        )

    @classmethod
    def _map_members(cls, result: GatewayMembersResult) -> OrganizationMembersResponse:
        return OrganizationMembersResponse(
            items=[cls._map_member(item) for item in result.items],
            page=MembersPage.model_validate(result.page.model_dump()),
        )

    @staticmethod
    def _map_member(member: GatewayMember) -> DirectoryMember:
        return DirectoryMember(
            id=member.id,
            display_name=member.name,
            avatar_url=member.avatar,
            account_status=member.account_status,
            employment_status=member.employment_status,
            enabled=member.enabled,
            departed=member.departed,
            primary_department=member.primary_department,
            departments=member.departments,
        )
