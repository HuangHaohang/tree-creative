import json
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tree_creative_api.modules.auth.domain import AuthenticatedUser, LoginTransaction
from tree_creative_api.modules.auth.models import (
    AuditEventModel,
    ExternalIdentityModel,
    UserModel,
)
from tree_creative_api.modules.auth.schemas import GatewayUser, ServerSession


class RedisLoginTransactionStore:
    def __init__(self, redis_client: object, key_prefix: str) -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix

    async def create(self, state: str, transaction: LoginTransaction, ttl_seconds: int) -> None:
        payload = json.dumps(
            {
                "redirect_uri": transaction.redirect_uri,
                "return_path": transaction.return_path,
                "created_at": transaction.created_at.isoformat(),
            },
            separators=(",", ":"),
        )
        await self._redis.set(self._key(state), payload, ex=ttl_seconds, nx=True)  # type: ignore[attr-defined]

    async def consume(self, state: str) -> LoginTransaction | None:
        payload = await self._redis.getdel(self._key(state))  # type: ignore[attr-defined]
        if payload is None:
            return None
        raw = json.loads(payload)
        return LoginTransaction(
            redirect_uri=str(raw["redirect_uri"]),
            return_path=str(raw.get("return_path", "/home")),
            created_at=datetime.fromisoformat(str(raw["created_at"])),
        )

    def _key(self, state: str) -> str:
        return f"{self._key_prefix}:login:{state}"


class RedisSessionStore:
    def __init__(self, redis_client: object, key_prefix: str) -> None:
        self._redis = redis_client
        self._key_prefix = key_prefix

    async def create(self, session: ServerSession, ttl_seconds: int) -> None:
        await self._redis.set(  # type: ignore[attr-defined]
            self._key(session.id),
            session.model_dump_json(by_alias=True),
            ex=ttl_seconds,
            nx=True,
        )

    async def get(self, session_id: str) -> ServerSession | None:
        payload = await self._redis.get(self._key(session_id))  # type: ignore[attr-defined]
        return None if payload is None else ServerSession.model_validate_json(payload)

    async def replace(self, session: ServerSession) -> bool:
        result = await self._redis.set(  # type: ignore[attr-defined]
            self._key(session.id),
            session.model_dump_json(by_alias=True),
            xx=True,
            keepttl=True,
        )
        return bool(result)

    async def revoke(self, session_id: str) -> None:
        await self._redis.delete(self._key(session_id))  # type: ignore[attr-defined]

    def _key(self, session_id: str) -> str:
        return f"{self._key_prefix}:session:{session_id}"


class SqlAlchemyUserRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def upsert_wps_user(self, user: GatewayUser, wps_company_id: str) -> AuthenticatedUser:
        now = datetime.now(UTC)
        tenant_id = wps_company_id or ""
        async with self._sessions.begin() as session:
            identity = await session.scalar(
                select(ExternalIdentityModel).where(
                    ExternalIdentityModel.provider == "wps",
                    ExternalIdentityModel.subject == user.id,
                    ExternalIdentityModel.tenant_id == tenant_id,
                )
            )
            if identity is None:
                model = UserModel(
                    id=str(uuid4()),
                    display_name=user.display_name,
                    avatar_url=user.avatar,
                    title=user.title,
                    employee_id=user.employee_id,
                    status=user.status,
                    created_at=now,
                    updated_at=now,
                )
                identity = ExternalIdentityModel(
                    id=str(uuid4()),
                    user=model,
                    provider="wps",
                    subject=user.id,
                    tenant_id=tenant_id,
                    claims=self._claims(user),
                    created_at=now,
                    updated_at=now,
                )
                session.add_all([model, identity])
            else:
                stored_model = await session.get(UserModel, identity.user_id)
                if stored_model is None:
                    raise RuntimeError("External identity references a missing user")
                model = stored_model
                model.display_name = user.display_name
                model.avatar_url = user.avatar
                model.title = user.title
                model.employee_id = user.employee_id
                model.status = user.status
                model.updated_at = now
                identity.claims = self._claims(user)
                identity.updated_at = now

        return AuthenticatedUser(
            id=model.id,
            display_name=model.display_name,
            avatar_url=model.avatar_url,
            organization_name=(
                user.primary_department.name if user.primary_department is not None else None
            ),
            title=model.title,
            employee_id=model.employee_id,
            status=model.status,
            permissions=frozenset(),
            wps_user_id=user.id,
            wps_company_id=wps_company_id,
        )

    @staticmethod
    def _claims(user: GatewayUser) -> dict[str, object]:
        return {
            "sourceRole": user.source_role,
            "departmentIds": [department.id for department in user.departments],
        }


class SqlAlchemyAuditRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def record(
        self,
        event_type: str,
        *,
        user_id: str | None,
        provider: str,
        occurred_at: datetime,
        details: dict[str, object] | None = None,
    ) -> None:
        async with self._sessions.begin() as session:
            session.add(
                AuditEventModel(
                    id=str(uuid4()),
                    event_type=event_type,
                    user_id=user_id,
                    provider=provider,
                    details=details or {},
                    occurred_at=occurred_at,
                )
            )
