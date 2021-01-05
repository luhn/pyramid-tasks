import functools
from contextlib import contextmanager

import celery
import venusian
from pyramid.scripting import prepare

from .settings import extract_celery_settings

# If set, pyramid_tasks will use this Celery application rather than make a new
# one.  This is necessary because when running a worker via an ini file (see
# celery.py), we need to create the app immediately but have no way of passing
# in the app when loading the app.
global_app = None


def set_global_app(app):
    global global_app
    global_app = app


def includeme(config):
    settings = config.get_settings()
    if global_app is None:
        app = celery.Celery(
            autofinalize=False,
            set_as_current=False,
        )
    else:
        app = global_app
    app.conf.update(extract_celery_settings(settings))
    app.pyramid_config = config
    config.registry["pyramid_tasks.app"] = app
    config.registry["pyramid_tasks.task_map"] = dict()
    config.add_directive("make_celery_app", make_celery_app)
    config.add_directive("register_task", register_task)
    config.action(
        ("celery", "finalize"),
        config.registry["pyramid_tasks.app"].finalize,
    )
    config.add_request_method(delay_task)
    config.add_request_method(get_task_result)


def make_celery_app(config):
    config.commit()
    return config.registry["pyramid_tasks.app"]


def register_task(config, func, **kwargs):
    """
    Register a new task with Celery.

    """
    wrapped = _wrap_task(func)
    task = config.registry["pyramid_tasks.app"].task(
        wrapped,
        bind=True,
        shared=False,
        **kwargs,
    )
    config.registry["pyramid_tasks.task_map"][func] = task


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
    env = prepare(registry=registry)
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


def delay_task(request, func_or_name, *args, **kwargs):
    """
    Add a task to the queue, for celery to pickup.  ``func_or_name`` can either
    by the name of the task (str) or the task function itself.

    """
    task_map = request.registry["pyramid_tasks.task_map"]
    if isinstance(func_or_name, str):
        celery_app = request.registry["pyramid_tasks.app"]
        task = celery_app.tasks[func_or_name]
    elif func_or_name in task_map:
        task = task_map[func_or_name]
    else:
        raise ValueError("Not a valid task.")
    return task.apply_async(args=args, kwargs=kwargs)


def get_task_result(request, task_id):
    """
    Get a result object from celery.

    """
    app = request.registry["pyramid_tasks.app"]
    return app.AsyncResult(task_id)
