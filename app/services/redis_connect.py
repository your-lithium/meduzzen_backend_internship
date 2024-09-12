from redis.asyncio import ConnectionPool, Redis

from app.core.config import config


class Redis_Client:
    def __init__(self):
        self.redis_pool = ConnectionPool(host=config.redis_host, port=config.redis_port)
        self.redis_client = None

    async def connect(self):
        self.redis_client = Redis(connection_pool=self.redis_pool)

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()

    async def setex(self, key, value, ttl):
        await self.redis_client.setex(key, ttl, value)

    async def get(self, key):
        value = await self.redis_client.get(key)
        return value


redis_client = Redis_Client()
