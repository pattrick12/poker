import os
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)

    async def close(self):
        await self.redis.close()

    def lock(self, name, timeout=5):
        return self.redis.lock(name, timeout=timeout)

    async def hset(self, name, mapping):
        return await self.redis.hset(name, mapping=mapping)
    
    async def get(self, name):
        return await self.redis.get(name)

# Global instance
redis_client = RedisClient()
# Expose the underlying redis object as 'redis' for compatibility with the prompt's usage
redis = redis_client.redis
