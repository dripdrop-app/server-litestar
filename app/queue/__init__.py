from typing import Callable

from litestar_saq import QueueConfig, SAQConfig
from saq import Job, Queue

from app.db import sqlalchemy_config
from app.queue import email
from app.queue.context import SAQContext
from app.settings import settings


async def startup(ctx: SAQContext):
    ctx["db_engine"] = sqlalchemy_config.get_engine()


async def shutdown(ctx: SAQContext):
    await ctx["db_engine"].dispose()


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


async def enqueue_task(
    queue: Queue, func: Callable, retries: int = 3, retry_backoff: bool = True, **kwargs
):
    matching_queues = [
        queue_config
        for queue_config in saq_config.queue_configs
        if func.__name__ in [task.__name__ for task in queue_config.tasks]
    ]
    if not matching_queues:
        raise Exception(f"{func.__name__} is not a registered task.")
    return await queue.enqueue(
        Job(func.__name__, kwargs=kwargs, retries=retries, retry_backoff=retry_backoff)
    )
