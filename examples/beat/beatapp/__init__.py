import os

from pyramid.config import Configurator


def configure(settings=None):
    if settings is None:
        settings = dict()

    # Optionally pull Redis URL from envvars
    redis_url = os.environ.get("REDIS_URL", "redis://")
    settings.setdefault("celery.broker_url", redis_url)
    settings.setdefault("celery.result_backend", redis_url)

    config = Configurator(settings=settings)
    config.include("pyramid_tasks")

    # Configure tasks
    config.register_task(print_message)
    config.add_periodic_task(5.0, print_message, ("PING",))

    return config


def application(global_config, **settings):
    return configure(settings).make_wsgi_app()


def print_message(request, message):
    print(message)
