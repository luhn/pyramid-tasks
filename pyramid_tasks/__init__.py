import celery
import venusian
from pyramid.interfaces import PHASE1_CONFIG, PHASE2_CONFIG, PHASE3_CONFIG

from .settings import extract_celery_settings
from .tweens import REQUEST_TWEEN, ITaskTweens, add_task_tween

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
    config.add_directive(
        "add_periodic_task", add_periodic_task, action_wrap=True
    )
    config.add_directive("add_task_tween", add_task_tween, action_wrap=True)
    config.add_task_tween(REQUEST_TWEEN)
    config.action(
        ("celery", "finalize"),
        config.registry["pyramid_tasks.app"].finalize,
        order=PHASE2_CONFIG,
    )
    config.add_request_method(delay_task)
    config.add_request_method(get_task_result)


def make_celery_app(config):
    config.commit()
    return config.registry["pyramid_tasks.app"]


def register_task(config, func, name=None, **kwargs):
    """
    Register a new task with Celery.

    """
    registry = config.registry
    app = registry["pyramid_tasks.app"]
    name = name or app.gen_task_name(func.__name__, func.__module__)

    def register():
        tweens = registry.queryUtility(ITaskTweens)
        if tweens:
            handler = tweens(func, registry)
        else:
            handler = func
        task = app.task(
            handler,
            name=name,
            shared=False,
            **kwargs,
        )
        config.registry["pyramid_tasks.task_map"][func] = task

    discriminator = ("register task", name)
    config.action(discriminator, register, order=PHASE1_CONFIG)


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


def _get_task(registry, func_or_name):
    """
    Get task by function or name.

    """
    task_map = registry["pyramid_tasks.task_map"]
    if isinstance(func_or_name, str):
        celery_app = registry["pyramid_tasks.app"]
        return celery_app.tasks[func_or_name]
    elif func_or_name in task_map:
        return task_map[func_or_name]
    else:
        raise ValueError("Not a valid task.")


def delay_task(request, func_or_name, *args, **kwargs):
    """
    Add a task to the queue, for celery to pickup.  ``func_or_name`` can either
    by the name of the task (str) or the task function itself.

    """
    task = _get_task(request.registry, func_or_name)
    return task.apply_async(args=args, kwargs=kwargs)


def add_periodic_task(
    config, schedule, func_or_name, args=(), kwargs=None, **opts
):
    """
    Add a period task.

    """

    def add():
        task = _get_task(config.registry, func_or_name)
        app = config.registry["pyramid_tasks.app"]
        app.add_periodic_task(schedule, task, args, kwargs, **opts)

    config.action(None, add, order=PHASE3_CONFIG)


def get_task_result(request, task_id):
    """
    Get a result object from celery.

    """
    app = request.registry["pyramid_tasks.app"]
    return app.AsyncResult(task_id)
