import asyncio
from dataclasses import dataclass
from typing import Protocol


class HealthProbe(Protocol):
    @property
    def name(self) -> str: ...

    async def check(self) -> None: ...


@dataclass(frozen=True, slots=True)
class ReadinessSnapshot:
    status: str
    dependencies: dict[str, str]


class ReadinessService:
    def __init__(self, probes: list[HealthProbe], timeout_seconds: float = 2.0) -> None:
        self._probes = probes
        self._timeout_seconds = timeout_seconds

    async def _check_probe(self, probe: HealthProbe) -> tuple[str, str]:
        try:
            async with asyncio.timeout(self._timeout_seconds):
                await probe.check()
        except Exception:  # A readiness endpoint must aggregate dependency failures.
            return probe.name, "unavailable"
        return probe.name, "ok"

    async def check(self) -> ReadinessSnapshot:
        results = await asyncio.gather(*(self._check_probe(probe) for probe in self._probes))
        dependencies = dict(results)
        status = "ok" if all(value == "ok" for value in dependencies.values()) else "degraded"
        return ReadinessSnapshot(status=status, dependencies=dependencies)
