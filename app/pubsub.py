import asyncio
from contextlib import asynccontextmanager

from redis.asyncio import Redis

from app.settings import settings


class PubSub:
    class Channels:
        MUSIC_JOB_UPDATE = "MUSIC_JOB_UPDATE"
        YOUTUBE_CHANNEL_UPDATE = "YOUTUBE_CHANNEL_UPDATE"

    def __init__(self, channels: list[str]):
        self.channels = channels

    @asynccontextmanager
    async def _get_redis(self):
        redis = Redis.from_url(settings.redis_url)
        try:
            yield redis
        finally:
            await redis.aclose()

    async def listen(self, ignore_subscribe_messages=False, timeout=60):
        async with self._get_redis() as redis:
            pubsub = redis.pubsub()
            await pubsub.subscribe(*self.channels)
            self._listen = True
            while self._listen:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=False, timeout=timeout
                )
                if (
                    ignore_subscribe_messages
                    and message
                    and message["type"] == "subscribe"
                ):
                    continue
                yield message
            await pubsub.unsubscribe()

    def stop_listening(self):
        self._listen = False

    async def publish_message(self, message: str):
        async with self._get_redis() as redis:
            encoded_message = message.encode()
            await asyncio.gather(
                *[
                    redis.publish(channel=channel, message=encoded_message)
                    for channel in self.channels
                ]
            )

    async def close(self):
        await self.close()
