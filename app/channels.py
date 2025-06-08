from litestar.channels.backends.redis import RedisChannelsPubSubBackend
from redis.asyncio import Redis

from app.settings import settings

MUSIC_JOB_UPDATE = "MUSIC_JOB_UPDATE"
YOUTUBE_CHANNEL_UPDATE = "YOUTUBE_CHANNEL_UPDATE"

redis = Redis.from_url(settings.redis_url)
channels_backend = RedisChannelsPubSubBackend(redis=redis)


async def publish_message(channel: str, message: str):
    await channels_backend.publish(channels=[channel], data=message.encode())
