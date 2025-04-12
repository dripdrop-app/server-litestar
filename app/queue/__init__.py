from typing import Callable

from litestar_saq import QueueConfig, SAQConfig
from redis.asyncio import Redis
from saq import Job, Queue

from app.db import sqlalchemy_config
from app.queue import email
from app.queue.context import SAQContext
from app.settings import settings


async def startup(ctx: SAQContext):
    ctx["db_engine"] = sqlalchemy_config.get_engine()
    ctx["redis"] = Redis.from_url(settings.redis_url)


async def shutdown(ctx: SAQContext):
    await ctx["db_engine"].dispose()
    await ctx["redis"].aclose()


saq_config = SAQConfig(
    queue_configs=[
        QueueConfig(
            dsn=settings.redis_url,
            tasks=[*email.tasks],
            startup=startup,
            shutdown=shutdown,
        )
    ],
    web_enabled=True,
)


def _is_registered_task(func: Callable):
    return [
        queue_config
        for queue_config in saq_config.queue_configs
        if func.__qualname__ in [task.__qualname__ for task in queue_config.tasks]
    ]


async def enqueue_task(
    queue: Queue, func: Callable, retries: int = 3, retry_backoff: bool = True, **kwargs
):
    if not _is_registered_task(func=func):
        raise Exception(f"{func.__qualname__} is not a registered task.")

    return await queue.enqueue(
        Job(
            func.__qualname__,
            kwargs=kwargs,
            retries=retries,
            retry_backoff=retry_backoff,
        )
    )
