import redis
from app.core.config import settings
r = redis.Redis(
  host=settings.REDIS_HOST,
  port=settings.REDIS_PORT,
  password=settings.REDIS_PASSWORD)

async def get_cached_data(key: str):
    return await r.get(key)

async def set_cached_data(key: str, value: str, expiration: int = 3600):
    await r.set(key, value, ex=expiration)
