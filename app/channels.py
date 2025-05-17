from litestar.channels.backends.memory import MemoryChannelsBackend
from litestar.channels.backends.redis import RedisChannelsPubSubBackend
from redis.asyncio import Redis

from app.settings import ENV, settings

MUSIC_JOB_UPDATE = "MUSIC_JOB_UPDATE"
YOUTUBE_CHANNEL_UPDATE = "YOUTUBE_CHANNEL_UPDATE"

redis_channels_backend = RedisChannelsPubSubBackend(
    redis=Redis.from_url(settings.redis_url)
)
memory_channels_backend = MemoryChannelsBackend()

channels_backend = (
    redis_channels_backend if settings.env != ENV.TESTING else memory_channels_backend
)


async def publish_message(channel: str, message: str):
    await channels_backend.on_startup()
    await channels_backend.publish(data=message, channels=[channel])
    await channels_backend.on_shutdown()
