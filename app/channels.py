from enum import Enum

from litestar.channels.backends.redis import RedisChannelsPubSubBackend
from redis.asyncio import Redis

from app.settings import settings


class Channels(Enum):
    MUSIC_JOB_UPDATE = "MUSIC_JOB_UPDATE"
    YOUTUBE_CHANNEL_UPDATE = "YOUTUBE_CHANNEL_UPDATE"


channels_backend = RedisChannelsPubSubBackend(redis=Redis(settings.redis_url))
