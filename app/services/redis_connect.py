from redis.asyncio import ConnectionPool, Redis

from app.core.config import config


class Redis_Client:
    def __init__(self):
        self.redis_pool = ConnectionPool(host=config.redis_host,
                                         port=config.redis_port,
                                         password=config.redis_password)
        self.redis_client = None

    async def connect(self):
        self.redis_client = Redis.from_pool(self.redis_pool)

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()


redis_client = Redis_Client()
