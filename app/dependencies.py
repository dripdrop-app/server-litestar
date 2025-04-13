from redis.asyncio import Redis

from app.settings import settings


async def provide_redis():
    redis_client = Redis.from_url(settings.redis_url)
    try:
        yield redis_client
    except Exception:
        await redis_client.aclose()
