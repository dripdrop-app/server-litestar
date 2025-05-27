import asyncio
from contextlib import asynccontextmanager

from celery import Task
from redis.asyncio import Redis

from app.db import sqlalchemy_config
from app.settings import settings


class QueueTask(Task):
    @asynccontextmanager
    async def db_session(self):
        async with sqlalchemy_config.get_session() as session:
            yield session

    @asynccontextmanager
    async def redis_client(self):
        redis_client = Redis.from_url(settings.redis_url)
        try:
            yield redis_client
        finally:
            await redis_client.aclose()

    def __call__(self, *args, **kwargs):
        try:
            loop = asyncio.get_running_loop()
            return loop.create_task(self.run(*args, **kwargs))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            return loop.run_until_complete(self.run(*args, **kwargs))
