import os
from time import sleep

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPBadRequest, HTTPCreated
from redis import Redis


def configure(settings=None):
    if settings is None:
        settings = dict()

    # Optionally pull Redis URL from envvars
    redis_url = os.environ.get("REDIS_URL", "redis://")
    settings.setdefault("redis.url", redis_url)
    settings.setdefault("celery.broker_url", redis_url)
    settings.setdefault("celery.result_backend", redis_url)

    config = Configurator(settings=settings)
    config.include("pyramid_tasks")
    configure_redis(config)

    # Configure views
    config.add_route("append", "/append")
    config.add_view(append, route_name="append", renderer="string")
    config.add_route("total", "/total")
    config.add_view(total, route_name="total", renderer="string")
    config.add_route("result", "/result")
    config.add_view(result, route_name="result", renderer="string")

    # Configure tasks
    config.register_task(total_task)

    return config


def application(global_config, **settings):
    return configure(settings).make_wsgi_app()


def configure_redis(config):
    """Add a `redis` property to the request."""
    settings = config.get_settings()
    redis = Redis.from_url(settings["redis.url"])
    config.add_request_method(lambda _: redis, "redis", property=True)


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
    request.redis.rpush("ledger", str(value))
    return "Done.\n"


def total(context, request):
    """
    Dispatch a task to total the ledger.

    """
    try:
        delay = float(request.GET.get("delay", "0"))
    except ValueError:
        raise HTTPBadRequest("`delay` must be a float.")
    result = request.delay_task(total_task, delay)
    return f"{ result.id }\n"


def total_task(request, delay=0.0):
    """
    A task to total the ledger.

    """
    sleep(delay)
    values = request.redis.lrange("ledger", 0, -1)
    return sum((int(val.decode("ascii")) for val in values), 0)


def result(context, request):
    """
    Get result of the task.

    """
    result = request.get_task_result(request.GET["id"])
    if result.ready():
        return f"{ result.result }\n"
    else:
        return "Pending...\n"
