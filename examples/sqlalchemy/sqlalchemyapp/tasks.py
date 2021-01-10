import os

from sqlalchemy import func

from .models import Ledger


def includeme(config):
    redis_url = os.environ.get("REDIS_URL", "redis://")
    settings = config.get_settings()
    if "celery.broker_url" not in settings:
        config.add_settings({"celery.broker_url": redis_url})
    if "celery.result_backend" not in settings:
        config.add_settings({"celery.result_backend": redis_url})

    config.include("pyramid_tasks")
    config.include("pyramid_tasks.transaction")

    config.register_task(total_task, name="total_task")


def total_task(request):
    return request.db.query(func.sum(Ledger.amount)).scalar() or 0
