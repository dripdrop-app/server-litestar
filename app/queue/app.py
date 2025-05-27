from celery import Celery

from app.settings import settings

celery = Celery(
    "tasks",
    broker=settings.redis_url,
    task_cls="app.queue.task.QueueTask",
)
celery.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    result_backend_always_retry=True,
    result_backend_max_retries=3,
)
