from redis.asyncio import Redis


class RedisCache:
    def __init__(self, url: str) -> None:
        self.client: Redis = Redis.from_url(url, decode_responses=True)

    async def ping(self) -> None:
        await self.client.ping()

    async def close(self) -> None:
        await self.client.aclose()
