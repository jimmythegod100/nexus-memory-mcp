import logging
from typing import Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisCache:
    def __init__(self, url: str) -> None:
        self.url = url
        self.client: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        self.client = aioredis.from_url(self.url, decode_responses=True)

    async def disconnect(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None

    async def get(self, key: str) -> Optional[str]:
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> bool:
        if not self.client:
            raise RuntimeError("Redis client not initialized")
        if ttl_seconds:
            await self.client.setex(key, ttl_seconds, value)
        else:
            await self.client.set(key, value)
        return True

    async def ping(self) -> bool:
        if not self.client:
            return False
        try:
            return await self.client.ping()
        except Exception as exc:
            logger.warning("Redis ping failed: %s", exc)
            return False
