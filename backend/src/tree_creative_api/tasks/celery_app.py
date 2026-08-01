from celery import Celery

from tree_creative_api.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "tree_creative",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["tree_creative_api.tasks.system"],
)
celery_app.conf.update(
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    result_accept_content=["json"],
    result_expires=86_400,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    task_soft_time_limit=1_740,
    task_time_limit=1_800,
    task_track_started=True,
    timezone="UTC",
    worker_prefetch_multiplier=1,
)
