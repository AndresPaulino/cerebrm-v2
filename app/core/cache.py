import aioredis
from app.core.config import settings

redis = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

async def get_cached_data(key):
    return await redis.get(key)

async def set_cached_data(key, value, expiration=3600):  # Cache for 1 hour by default
    await redis.set(key, value, ex=expiration)