import asyncio
from redis.asyncio import Redis

from config import CONFIG


class RedisClientError(Exception):
    ...


class _RedisClient:
    def __init__(self):
        self.client = None


    def connect(self):
        try:
            self.client = Redis(
                host=CONFIG.REDIS_HOST,
                port=CONFIG.REDIS_PORT,
                password=CONFIG.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
            )
        
        except Exception as e:
            raise RedisClientError(f"Error while connecting to the Redis Client: ")


    async def get(self, key: str):
        if not self.client:
            raise RedisClientError(f"Redis Client not initialized. Initialize the Redis Client first.")
        try:
            return await self.client.get(key)

        except Exception as e:
            raise RedisClientError(f"Error while fetching key from the Redis: ")


    async def set(self, key: str, value: str, ex: int = None):
        if not self.client:
            raise RedisClientError(f"Redis Client not initialized. Initialize the Redis Client first.")
        try:
            await self.client.set(key=key, value=value, ex=ex)

        except Exception as e:
            raise RedisClientError(f"Error while fetching key from the Redis: ")


    async def delete(self, key: str):
        if not self.client:
            raise RedisClientError(f"Redis Client not initialized. Initialize the Redis Client first.")
        try:
            await self.client.delete(key=key)

        except Exception as e:
            raise RedisClientError(f"Error while fetching key from the Redis: ")


RedisClient = _RedisClient()
