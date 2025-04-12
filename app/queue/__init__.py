from litestar_saq import QueueConfig, SAQConfig

from app.db import sqlalchemy_config
from app.queue import email
from app.queue.context import SAQContext
from app.settings import settings


async def startup(ctx: SAQContext):
    ctx["db_engine"] = sqlalchemy_config.get_engine()


async def shutdown(ctx: SAQContext):
    await ctx["db_engine"].dispose()


saq_config = SAQConfig(
    dsn=settings.redis_url,
    queue_configs=[
        QueueConfig(tasks=[*email.tasks], startup=startup, shutdown=shutdown)
    ],
    web_enabled=True,
)
