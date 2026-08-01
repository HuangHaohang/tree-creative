from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CallableProbe:
    name: str
    check_function: Callable[[], Awaitable[None]]

    async def check(self) -> None:
        await self.check_function()
