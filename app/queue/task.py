import asyncio
from contextlib import asynccontextmanager

from celery import Task
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.settings import settings


class QueueTask(Task):
    @asynccontextmanager
    async def db_session(self):
        engine = create_async_engine(settings.async_database_url)
        sessionmaker = async_sessionmaker(engine)
        async with sessionmaker() as session:
            yield session
        await engine.dispose()

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
