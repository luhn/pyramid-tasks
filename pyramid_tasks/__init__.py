import functools
from contextlib import contextmanager

import celery
import pyramid
import venusian

from .settings import extract_celery_settings


def includeme(config):
    settings = config.get_settings()
    app = celery.Celery(
        settings["tasks.name"],
        autofinalize=False,
        set_as_current=False,
    )
    app.conf.update(extract_celery_settings(settings))
    app.pyramid_config = config
    config.registry["pyramid_tasks.app"] = app
    config.registry["pyramid_tasks.task_map"] = dict()
    config.add_directive("make_celery_app", _get_celery_app)
    config.add_directive("register_task", register_task)
    config.action(
        ("celery", "finalize"),
        config.registry["pyramid_tasks.app"].finalize,
    )
    config.add_request_method(delay)


def _get_celery_app(config):
    return config.registry["pyramid_tasks.app"]


def register_task(config, func, **kwargs):
    """
    Register a new task with Celery.

    """
    wrapped = _wrap_task(func)
    task = config.registry["celery.app"].task(
        wrapped,
        bind=True,
        shared=False,
        **kwargs,
    )
    config.registry["celery.task_map"][func] = task


def _wrap_task(func):
    """
    Inject a Pyramid request into the task arguments.

    """

    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        with _task_request(self) as request:
            return func(request, *args, **kwargs)

    return wrapped


@contextmanager
def _task_request(task):
    """
    Create a new Pyramid request from a Celery task.

    """
    registry = task.app.pyramid_config.registry
    env = pyramid.scripting.prepare(registry=registry)
    try:
        yield env["request"]
    finally:
        env["request"]._process_finished_callbacks()
        env["closer"]()


def task(**kwargs):
    """
    Decorator to register a new task.

    """

    def wrapper(func):
        def callback(scanner, name, wrapped):
            scanner.config.register_task(wrapped, **kwargs)

        venusian.attach(func, callback)
        return func

    return wrapper


def delay(request, func_or_name, *args, **kwargs):
    """
    Add a task to the queue, for celery to pickup.  ``func_or_name`` can either
    by the name of the task (str) or the task function itself.

    """
    task_map = request.registry["celery.task_map"]
    if isinstance(func_or_name, str):
        celery_app = request.registry["celery.app"]
        task = celery_app.tasks[func_or_name]
    elif func_or_name in task_map:
        task = task_map[func_or_name]
    else:
        raise ValueError("Not a valid task.")
    return task.apply_async(args=args, kwargs=kwargs)
