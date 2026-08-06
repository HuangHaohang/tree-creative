from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from tree_creative_api.api.dependencies import get_authentication_service
from tree_creative_api.core.config import Settings
from tree_creative_api.core.errors import ApiError
from tree_creative_api.infrastructure.wps_gateway import (
    WpsGatewayUnavailableError,
    WpsTokenInvalidError,
)
from tree_creative_api.main import create_app
from tree_creative_api.modules.auth.domain import AuthenticatedUser, LoginTransaction
from tree_creative_api.modules.auth.schemas import (
    DepartmentReference,
    GatewayDepartmentNode,
    GatewayDepartmentTree,
    GatewayMember,
    GatewayMemberPage,
    GatewayMembersResult,
    GatewayTokenRefresh,
    GatewayTokenVerification,
    GatewayTreeUserStats,
    GatewayUser,
    ServerSession,
    SessionUser,
    WpsCallbackPayload,
)
from tree_creative_api.modules.auth.service import AuthenticationService

NOW = datetime(2026, 8, 3, 6, 0, tzinfo=UTC)


class MutableClock:
    def __init__(self) -> None:
        self.value = NOW

    def __call__(self) -> datetime:
        return self.value


class InMemoryLoginTransactions:
    def __init__(self, now: Callable[[], datetime]) -> None:
        self._now = now
        self.items: dict[str, tuple[LoginTransaction, datetime]] = {}

    async def create(self, state: str, transaction: LoginTransaction, ttl_seconds: int) -> None:
        self.items[state] = (transaction, self._now() + timedelta(seconds=ttl_seconds))

    async def consume(self, state: str) -> LoginTransaction | None:
        entry = self.items.pop(state, None)
        if entry is None or entry[1] <= self._now():
            return None
        return entry[0]


class InMemorySessions:
    def __init__(self) -> None:
        self.items: dict[str, ServerSession] = {}
        self.replaced_envelopes: list[str] = []

    async def create(self, session: ServerSession, ttl_seconds: int) -> None:
        assert ttl_seconds > 0
        self.items[session.id] = session

    async def get(self, session_id: str) -> ServerSession | None:
        return self.items.get(session_id)

    async def replace(self, session: ServerSession) -> bool:
        if session.id not in self.items:
            return False
        self.items[session.id] = session
        self.replaced_envelopes.append(session.token_envelope)
        return True

    async def revoke(self, session_id: str) -> None:
        self.items.pop(session_id, None)


class InMemoryUsers:
    async def upsert_wps_user(self, user: GatewayUser, wps_company_id: str) -> AuthenticatedUser:
        return AuthenticatedUser(
            id="internal-user-1",
            display_name=user.display_name,
            avatar_url=user.avatar,
            organization_name=user.primary_department.name if user.primary_department else None,
            title=user.title,
            employee_id=user.employee_id,
            status=user.status,
            permissions=frozenset({"organization:read"}),
            wps_user_id=user.id,
            wps_company_id=wps_company_id,
        )


class InMemoryAudits:
    def __init__(self) -> None:
        self.events: list[str] = []

    async def record(
        self,
        event_type: str,
        *,
        user_id: str | None,
        provider: str,
        occurred_at: datetime,
        details: dict[str, object] | None = None,
    ) -> None:
        assert provider == "wps"
        assert occurred_at.tzinfo is not None
        assert details is None or "tokenEnvelope" not in details
        self.events.append(event_type)


class FakeGateway:
    def __init__(self) -> None:
        self.user = GatewayUser(
            id="wps-user-1",
            display_name="测试用户",
            avatar="https://example.test/avatar.png",
            status="active",
            title="产品经理",
            employee_id="E-001",
            primary_department=DepartmentReference(
                id="dept-product",
                name="产品部",
                path="/公司/产品部",
                is_primary=True,
            ),
        )
        self.verify_result = GatewayTokenVerification(active=True)
        self.refresh_result = GatewayTokenRefresh(
            token_envelope="replacement-envelope",
            token_type="wps_token_envelope",
            access_expires_at=NOW + timedelta(hours=2),
            refresh_expires_at=NOW + timedelta(days=7),
        )
        self.verify_error: Exception | None = None
        self.refresh_error: Exception | None = None
        self.last_envelope: str | None = None
        self.last_department_id: str | None = None
        self.last_page_size: int | None = None
        self.last_keyword: str | None = None

    async def get_current_user(self, token_envelope: str) -> GatewayUser:
        self.last_envelope = token_envelope
        return self.user

    async def verify_token(self, token_envelope: str) -> GatewayTokenVerification:
        self.last_envelope = token_envelope
        if self.verify_error:
            raise self.verify_error
        return self.verify_result

    async def refresh_token(self, token_envelope: str) -> GatewayTokenRefresh:
        self.last_envelope = token_envelope
        if self.refresh_error:
            raise self.refresh_error
        return self.refresh_result

    async def get_department_tree(self, token_envelope: str) -> GatewayDepartmentTree:
        self.last_envelope = token_envelope
        return GatewayDepartmentTree(
            tree=GatewayDepartmentNode(
                id="root",
                name="公司",
                users=[],
                children=[
                    GatewayDepartmentNode(
                        id="dept-product",
                        name="产品部",
                        parent_id="root",
                        users=[self.user],
                    )
                ],
            ),
            users=GatewayTreeUserStats(total=1, attached=1, unassigned=[]),
        )

    async def list_members(
        self,
        token_envelope: str,
        *,
        page_size: int,
        cursor: str | None,
        department_id: str | None,
        include_subdepartments: bool,
    ) -> GatewayMembersResult:
        self.last_envelope = token_envelope
        self.last_department_id = department_id
        self.last_page_size = page_size
        assert page_size <= 100
        return self._members()

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
        assert keyword == "测试"
        self.last_keyword = keyword
        return await self.list_members(
            token_envelope,
            page_size=page_size,
            cursor=cursor,
            department_id=department_id,
            include_subdepartments=include_subdepartments,
        )

    @staticmethod
    def _members() -> GatewayMembersResult:
        return GatewayMembersResult(
            items=[GatewayMember(id="wps-user-1", name="测试用户", enabled=True)],
            page=GatewayMemberPage(page_size=20, has_more=False, total=1),
        )


def build_service(
    clock: MutableClock | None = None,
) -> tuple[AuthenticationService, InMemoryLoginTransactions, InMemorySessions, FakeGateway]:
    resolved_clock = clock or MutableClock()
    login_transactions = InMemoryLoginTransactions(resolved_clock)
    sessions = InMemorySessions()
    gateway = FakeGateway()
    service = AuthenticationService(
        gateway=gateway,
        login_transactions=login_transactions,
        sessions=sessions,
        users=InMemoryUsers(),
        audits=InMemoryAudits(),
        gateway_base_url="https://gateway.example.test",
        client_service="tree-creative",
        redirect_uri="http://localhost:8000/api/oauth/callback",
        frontend_base_url="http://localhost:8080",
        login_state_ttl_seconds=600,
        session_ttl_seconds=28_800,
        token_verify_interval_seconds=300,
        token_refresh_leeway_seconds=120,
        now=resolved_clock,
    )
    return service, login_transactions, sessions, gateway


def callback(state: str, **updates: object) -> WpsCallbackPayload:
    payload: dict[str, object] = {
        "tokenType": "wps_token_envelope",
        "tokenEnvelope": "opaque-envelope",
        "state": state,
        "accessExpiresAt": NOW + timedelta(hours=1),
        "refreshExpiresAt": NOW + timedelta(days=7),
        "wpsUserId": "wps-user-1",
        "wpsCompanyId": "wps-company-1",
    }
    payload.update(updates)
    return WpsCallbackPayload.model_validate(payload)


async def establish_session(service: AuthenticationService) -> ServerSession:
    login_url = await service.begin_wps_login()
    state = parse_qs(urlparse(login_url).query)["state"][0]
    completed = await service.complete_wps_login(callback(state))
    return completed.session


def server_session() -> ServerSession:
    return ServerSession(
        id="server-session-1",
        csrf_token="csrf-token-1",
        token_envelope="opaque-envelope",
        access_expires_at=NOW + timedelta(hours=1),
        refresh_expires_at=NOW + timedelta(days=7),
        verified_at=NOW,
        created_at=NOW,
        user=SessionUser(
            id="internal-user-1",
            display_name="测试用户",
            avatar_url=None,
            organization_name="产品部",
            status="active",
            permissions=["organization:read"],
            wps_user_id="wps-user-1",
            wps_company_id="wps-company-1",
        ),
    )


@pytest.mark.asyncio
async def test_login_state_is_random_single_use_and_expires() -> None:
    clock = MutableClock()
    service, transactions, _, _ = build_service(clock)
    first_url = await service.begin_wps_login()
    second_url = await service.begin_wps_login()
    first_query = parse_qs(urlparse(first_url).query)
    second_query = parse_qs(urlparse(second_url).query)

    assert first_query["state"] != second_query["state"]
    assert first_query["client_service"] == ["tree-creative"]
    assert first_query["response_mode"] == ["form_post"]

    first_state = first_query["state"][0]
    await service.complete_wps_login(callback(first_state))
    with pytest.raises(ApiError, match="already used"):
        await service.complete_wps_login(callback(first_state))

    expired_state = next(iter(transactions.items))
    clock.value += timedelta(minutes=11)
    with pytest.raises(ApiError, match="expired"):
        await service.complete_wps_login(callback(expired_state))


@pytest.mark.asyncio
async def test_session_refresh_replaces_envelope_atomically() -> None:
    clock = MutableClock()
    service, _, sessions, gateway = build_service(clock)
    session = await establish_session(service)
    expiring = session.model_copy(update={"access_expires_at": NOW + timedelta(seconds=30)})
    sessions.items[session.id] = expiring

    refreshed = await service.require_session(session.id)

    assert refreshed.token_envelope == "replacement-envelope"
    assert sessions.replaced_envelopes == ["replacement-envelope"]
    assert gateway.last_envelope == "opaque-envelope"


@pytest.mark.asyncio
async def test_permanent_token_failure_revokes_but_temporary_failure_preserves_session() -> None:
    service, _, sessions, gateway = build_service()
    session = await establish_session(service)
    sessions.items[session.id] = session.model_copy(
        update={"access_expires_at": NOW + timedelta(seconds=30)}
    )
    gateway.refresh_error = WpsGatewayUnavailableError("temporary")

    with pytest.raises(ApiError) as temporary_error:
        await service.require_session(session.id)
    assert temporary_error.value.status_code == 503
    assert session.id in sessions.items

    gateway.refresh_error = WpsTokenInvalidError("invalid")
    with pytest.raises(ApiError) as invalid_error:
        await service.require_session(session.id)
    assert invalid_error.value.status_code == 401
    assert session.id not in sessions.items


def test_me_logout_and_protected_routes_use_real_server_session() -> None:
    service, _, sessions, _ = build_service()
    app = create_app(Settings(app_env="test"))
    app.dependency_overrides[get_authentication_service] = lambda: service

    with TestClient(app) as client:
        session = server_session()
        sessions.items[session.id] = session
        client.cookies.set("tree_creative_session", session.id)

        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["user"]["displayName"] == "测试用户"
        csrf_token = me.json()["csrfToken"]

        tree = client.get("/api/organization/tree")
        assert tree.status_code == 200
        assert tree.json()["tree"]["children"][0]["users"][0]["displayName"] == "测试用户"
        assert "tokenEnvelope" not in tree.text

        logout = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})
        assert logout.status_code == 204
        assert session.id not in sessions.items

        client.cookies.set("tree_creative_session", session.id)
        assert client.get("/api/auth/me").status_code == 401
        assert client.get("/api/organization/tree").status_code == 401
        assert client.post("/api/auth/logout").status_code == 204


def test_http_callback_creates_only_an_opaque_cookie_and_redirects_safely() -> None:
    service, _, sessions, _ = build_service()
    app = create_app(Settings(app_env="test"))
    app.dependency_overrides[get_authentication_service] = lambda: service

    with TestClient(app) as client:
        login = client.get(
            "/api/auth/wps/login",
            params={"returnTo": "/organization?departmentId=product"},
            follow_redirects=False,
        )
        state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
        response = client.post(
            "/api/oauth/callback",
            data={
                "tokenType": "wps_token_envelope",
                "tokenEnvelope": "opaque-envelope",
                "state": state,
                "accessExpiresAt": (NOW + timedelta(hours=1)).isoformat(),
                "refreshExpiresAt": (NOW + timedelta(days=7)).isoformat(),
                "wpsUserId": "wps-user-1",
                "wpsCompanyId": "wps-company-1",
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == (
        "http://localhost:8080/organization?departmentId=product"
    )
    cookie = response.headers["set-cookie"]
    assert "tree_creative_session=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "opaque-envelope" not in cookie
    assert len(sessions.items) == 1


@pytest.mark.parametrize(
    "return_to",
    ["https://evil.example.test", "//evil.example.test", "/\\evil.example.test", "/login"],
)
def test_login_rejects_unsafe_return_paths(return_to: str) -> None:
    service, transactions, _, _ = build_service()
    app = create_app(Settings(app_env="test"))
    app.dependency_overrides[get_authentication_service] = lambda: service

    with TestClient(app) as client:
        response = client.get(
            "/api/auth/wps/login",
            params={"returnTo": return_to},
            follow_redirects=False,
        )

    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    assert transactions.items[state][0].return_path == "/home"


def test_logout_requires_csrf_for_an_existing_session() -> None:
    service, _, sessions, _ = build_service()
    app = create_app(Settings(app_env="test"))
    app.dependency_overrides[get_authentication_service] = lambda: service
    session = server_session()
    sessions.items[session.id] = session

    with TestClient(app) as client:
        client.cookies.set("tree_creative_session", session.id)
        response = client.post("/api/auth/logout")

    assert response.status_code == 403
    assert session.id in sessions.items


def test_personnel_routes_forward_camel_case_filters_to_the_gateway() -> None:
    service, _, sessions, gateway = build_service()
    app = create_app(Settings(app_env="test"))
    app.dependency_overrides[get_authentication_service] = lambda: service
    session = server_session()
    sessions.items[session.id] = session

    with TestClient(app) as client:
        client.cookies.set("tree_creative_session", session.id)
        members = client.get(
            "/api/organization/members",
            params={"departmentId": "dept-product", "pageSize": 25},
        )
        assert gateway.last_department_id == "dept-product"
        assert gateway.last_page_size == 25
        search = client.get(
            "/api/organization/members/search",
            params={"keyword": "测试", "departmentId": "dept-product"},
        )

    assert members.status_code == 200
    assert members.json()["items"][0]["displayName"] == "测试用户"
    assert search.status_code == 200
    assert gateway.last_department_id == "dept-product"
    assert gateway.last_page_size == 20
    assert gateway.last_keyword == "测试"


def test_callback_rejects_invalid_payload_without_echoing_envelope() -> None:
    service, _, _, _ = build_service()
    app = create_app(Settings(app_env="test"))
    app.dependency_overrides[get_authentication_service] = lambda: service

    with TestClient(app) as client:
        response = client.post(
            "/api/oauth/callback",
            data={"tokenType": "invalid", "tokenEnvelope": "sensitive-test-envelope"},
        )

    assert response.status_code == 400
    assert "sensitive-test-envelope" not in response.text
