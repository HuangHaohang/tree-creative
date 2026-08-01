from tree_creative_api.tasks.celery_app import celery_app


@celery_app.task(name="system.ping")
def ping() -> str:
    return "pong"
