from fastapi.testclient import TestClient

from tree_creative_api.api.dependencies import get_readiness_service
from tree_creative_api.core.config import Settings
from tree_creative_api.main import create_app
from tree_creative_api.modules.health.service import ReadinessService


class PassingProbe:
    name = "example"

    async def check(self) -> None:
        return None


def test_liveness() -> None:
    app = create_app(Settings(app_env="test"))

    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_uses_injected_probes() -> None:
    app = create_app(Settings(app_env="test"))
    app.dependency_overrides[get_readiness_service] = lambda: ReadinessService([PassingProbe()])

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json()["dependencies"] == {"example": "ok"}
