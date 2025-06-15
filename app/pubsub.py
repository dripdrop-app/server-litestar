import asyncio

from redis.asyncio import Redis

from app.settings import settings


class PubSub:
    class Channels:
        MUSIC_JOB_UPDATE = "MUSIC_JOB_UPDATE"
        YOUTUBE_CHANNEL_UPDATE = "YOUTUBE_CHANNEL_UPDATE"

    def __init__(self, channels: list[str]):
        self.redis = Redis.from_url(settings.redis_url)
        self.pubsub = self.redis.pubsub()
        self.channels = channels

    async def listen(self, ignore_subscribe_messages=False, timeout=60):
        await self.pubsub.subscribe(*self.channels)
        self._listen = True
        while self._listen:
            message = await self.pubsub.get_message(
                ignore_subscribe_messages=False, timeout=timeout
            )
            if ignore_subscribe_messages and message and message["type"] == "subscribe":
                continue
            yield message
        await self.pubsub.unsubscribe()

    def stop_listening(self):
        self._listen = False

    async def publish_message(self, message: str):
        encoded_message = message.encode()
        await asyncio.gather(
            *[
                self.redis.publish(channel=channel, message=encoded_message)
                for channel in self.channels
            ]
        )

    async def close(self):
        await self.close()
