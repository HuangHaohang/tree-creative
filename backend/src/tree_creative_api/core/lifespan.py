from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI

from tree_creative_api.core.config import Settings
from tree_creative_api.infrastructure.resources import ApplicationResources


def build_lifespan(
    settings: Settings,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None, bool | None]]:
    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        resources = ApplicationResources.create(settings)
        application.state.resources = resources
        application.state.readiness_service = resources.readiness_service()
        try:
            yield
        finally:
            await resources.close()

    return lifespan
