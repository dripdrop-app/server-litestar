from litestar_saq import QueueConfig, SAQConfig
from redis.asyncio import Redis
from saq import Job, Queue
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db import sqlalchemy_config
from app.queue.context import SAQContext
from app.settings import ENV, settings

tasks = [
    "app.queue.email.send_verification_email",
    "app.queue.email.send_password_reset_email",
    "app.queue.music.run_music_job",
]
on_fail_tasks = {"app.queue.music.run_music_job": "app.queue.music.on_failed_music_job"}


async def startup(ctx: SAQContext):
    ctx["db_engine"] = sqlalchemy_config.get_engine()
    ctx["db_sessionmaker"] = async_sessionmaker(ctx["db_engine"])
    ctx["redis"] = Redis.from_url(settings.redis_url)


async def shutdown(ctx: SAQContext):
    await ctx["db_engine"].dispose()
    await ctx["redis"].aclose()


async def after_process(ctx: SAQContext):
    job = ctx["job"]
    if job.attempts == job.retries:
        on_fail_task = on_fail_tasks.get(job.function)
        on_fail_task(ctx)


saq_config = SAQConfig(
    queue_configs=[
        QueueConfig(
            name="default",
            dsn=settings.redis_url,
            tasks=tasks,
            startup=startup,
            shutdown=shutdown,
            after_process=after_process,
        )
    ],
    web_enabled=True,
    use_server_lifespan=settings.env == ENV.TESTING,
)


async def enqueue_task(
    func: str,
    retries: int = 3,
    retry_backoff: bool = True,
    queue: Queue = None,
    **kwargs,
):
    if not queue:
        queue = saq_config.get_queues().get("default")

    return await queue.enqueue(
        Job(
            func,
            kwargs=kwargs,
            retries=retries,
            retry_backoff=retry_backoff,
        )
    )


async def apply_task(
    func: str,
    retries: int = 3,
    retry_backoff: bool = True,
    queue: Queue = None,
    **kwargs,
):
    if not queue:
        queue = saq_config.get_queues().get("default")

    return await queue.apply(
        Job(
            func,
            kwargs=kwargs,
            retries=retries,
            retry_backoff=retry_backoff,
        )
    )
