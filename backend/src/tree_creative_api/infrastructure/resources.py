from dataclasses import dataclass

from tree_creative_api.core.config import Settings
from tree_creative_api.infrastructure.cache import RedisCache
from tree_creative_api.infrastructure.database import Database
from tree_creative_api.infrastructure.object_storage import ObjectStorage
from tree_creative_api.modules.health.probes import CallableProbe
from tree_creative_api.modules.health.service import ReadinessService


@dataclass(slots=True)
class ApplicationResources:
    database: Database
    cache: RedisCache
    object_storage: ObjectStorage

    @classmethod
    def create(cls, settings: Settings) -> "ApplicationResources":
        return cls(
            database=Database(settings.mysql_url),
            cache=RedisCache(settings.redis_url),
            object_storage=ObjectStorage(
                endpoint=settings.minio_endpoint,
                access_key=settings.minio_access_key.get_secret_value(),
                secret_key=settings.minio_secret_key.get_secret_value(),
                secure=settings.minio_secure,
            ),
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
        await self.cache.close()
        await self.database.close()
