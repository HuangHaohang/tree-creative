from dataclasses import dataclass

import httpx

from tree_creative_api.core.config import Settings
from tree_creative_api.infrastructure.auth_storage import (
    RedisLoginTransactionStore,
    RedisSessionStore,
    SqlAlchemyAuditRepository,
    SqlAlchemyUserRepository,
)
from tree_creative_api.infrastructure.cache import RedisCache
from tree_creative_api.infrastructure.database import Database
from tree_creative_api.infrastructure.object_storage import ObjectStorage
from tree_creative_api.infrastructure.wps_gateway import WpsGatewayHttpClient
from tree_creative_api.modules.auth.service import AuthenticationService
from tree_creative_api.modules.health.probes import CallableProbe
from tree_creative_api.modules.health.service import ReadinessService


@dataclass(slots=True)
class ApplicationResources:
    database: Database
    cache: RedisCache
    object_storage: ObjectStorage
    http_client: httpx.AsyncClient
    auth_service: AuthenticationService

    @classmethod
    def create(cls, settings: Settings) -> "ApplicationResources":
        database = Database(settings.mysql_url)
        cache = RedisCache(settings.redis_url)
        http_client = httpx.AsyncClient(
            base_url=settings.wps_gateway_base_url,
            timeout=httpx.Timeout(10.0),
        )
        gateway = WpsGatewayHttpClient(
            http_client,
            client_service=settings.wps_gateway_client_service,
            client_secret=settings.wps_gateway_client_secret.get_secret_value(),
        )
        auth_service = AuthenticationService(
            gateway=gateway,
            login_transactions=RedisLoginTransactionStore(
                cache.client,
                settings.auth_redis_key_prefix,
            ),
            sessions=RedisSessionStore(cache.client, settings.auth_redis_key_prefix),
            users=SqlAlchemyUserRepository(database.sessions),
            audits=SqlAlchemyAuditRepository(database.sessions),
            gateway_base_url=settings.wps_gateway_base_url,
            client_service=settings.wps_gateway_client_service,
            redirect_uri=settings.wps_gateway_redirect_uri,
            frontend_base_url=settings.frontend_base_url,
            login_state_ttl_seconds=settings.auth_login_state_ttl_seconds,
            session_ttl_seconds=settings.auth_session_ttl_seconds,
            token_verify_interval_seconds=settings.auth_token_verify_interval_seconds,
            token_refresh_leeway_seconds=settings.auth_token_refresh_leeway_seconds,
        )
        return cls(
            database=database,
            cache=cache,
            object_storage=ObjectStorage(
                endpoint=settings.minio_endpoint,
                access_key=settings.minio_access_key.get_secret_value(),
                secret_key=settings.minio_secret_key.get_secret_value(),
                secure=settings.minio_secure,
            ),
            http_client=http_client,
            auth_service=auth_service,
        )

    def readiness_service(self) -> ReadinessService:
        return ReadinessService(
            probes=[
                CallableProbe(name="mysql", check_function=self.database.ping),
                CallableProbe(name="redis", check_function=self.cache.ping),
                CallableProbe(name="minio", check_function=self.object_storage.ping),
            ],
        )

    async def close(self) -> None:
        await self.http_client.aclose()
        await self.cache.close()
        await self.database.close()
