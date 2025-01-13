from redis import asyncio as aioredis
from redis.asyncio.client import Redis

from settings import get_app_settings


class RedisProvider:
    __redis: None | Redis = None

    @classmethod
    def init_redis(cls) -> None:
        redis_settings = get_app_settings()
        db_url = (
            f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}/0"
        )
        if not cls.__redis:
            cls.__redis = aioredis.from_url(db_url)

    @classmethod
    def get_redis(cls) -> Redis:
        if not cls.__redis:
            raise Exception("Redis client was not initialized")
        return cls.__redis
