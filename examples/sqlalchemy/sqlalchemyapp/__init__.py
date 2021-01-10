import os

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPBadRequest
from sqlalchemy import func

from .models import Ledger


def configure(settings=None):
    if settings is None:
        settings = dict()

    # Set config, optionally from envvars
    redis_url = os.environ.get("REDIS_URL", "redis://")
    settings.setdefault("celery.broker_url", redis_url)
    settings.setdefault("celery.result_backend", redis_url)
    settings.setdefault(
        "sqlalchemy.url",
        os.environ.get("SQLALCHEMY_URL", "sqlite:///database.db"),
    )

    config = Configurator(settings=settings)
    config.include("pyramid_tasks")
    config.include(".models")

    # Configure views
    config.add_route("append", "/append")
    config.add_view(append, route_name="append", renderer="string")
    config.add_route("total", "/total")
    config.add_view(total, route_name="total", renderer="string")

    # Configure tasks
    config.register_task(total_task)

    return config


def application(global_config, **settings):
    return configure(settings).make_wsgi_app()


def append(context, request):
    """
    Append a value to the ledger.

    """
    try:
        value = int(request.params["value"])
    except KeyError:
        raise HTTPBadRequest("Must include `value`.")
    except ValueError:
        raise HTTPBadRequest("`value` must be an integer.")
    request.db.add(Ledger(amount=value))
    return "Done.\n"


def total(context, request):
    """
    Calculate the total.

    """
    result = request.delay_task(total_task).get()
    return f"{ result }\n"


def total_task(request):
    return request.db.query(func.sum(Ledger.amount)).scalar() or 0
