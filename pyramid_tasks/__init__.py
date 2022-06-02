import celery
import venusian
from pyramid.interfaces import PHASE1_CONFIG, PHASE2_CONFIG, PHASE3_CONFIG
from pyramid.scripting import prepare

from .events import BeforeDeferTask, CeleryWorkerProcessInit
from .settings import extract_celery_settings
from .taskderivers import apply_task_derivers

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
    _connect_worker_process_init(config.registry)
    app.conf.update(extract_celery_settings(settings))
    app.pyramid_config = config
    config.registry["pyramid_tasks.app"] = app
    config.registry["pyramid_tasks.task_map"] = dict()
    config.add_directive("make_celery_app", make_celery_app)
    config.add_directive("register_task", register_task)
    config.add_directive(
        "add_periodic_task", add_periodic_task, action_wrap=True
    )
    config.action(
        ("celery", "finalize"),
        _get_app(config.registry).finalize,
        order=PHASE2_CONFIG,
    )
    config.add_request_method(defer_task)
    config.add_request_method(defer_task_with_options)
    config.add_request_method(defer_task, "delay_task")  # Legacy
    config.add_request_method(get_task_result)
    config.add_request_method(current_task, property=True)
    config.include(".taskderivers")


def _get_app(registry):
    return registry["pyramid_tasks.app"]


def make_celery_app(config):
    config.commit()
    return _get_app(config.registry)


def register_task(config, func, name=None, **kwargs):
    """
    Register a new task with Celery.

    """
    registry = config.registry
    app = _get_app(registry)
    name = name or app.gen_task_name(func.__name__, func.__module__)

    def register():
        derived = apply_task_derivers(config, func, name, kwargs)
        handler = _make_task_handler(config.registry, derived)
        task = app.task(
            handler,
            name=name,
            shared=False,
            **kwargs,
        )
        config.registry["pyramid_tasks.task_map"][func] = task

    discriminator = ("register task", name)
    config.action(discriminator, register, order=PHASE1_CONFIG)


def _make_task_handler(registry, func):
    """
    Return a task handler that creates a new request and injects it as the
    first positional argument in the wrapped function.

    """

    def handler(*args, **kwargs):
        with prepare(registry=registry) as env:
            return func(env["request"], *args, **kwargs)

    return handler


def task(**kwargs):
    """
    Decorator to register a new task.

    """

    def wrapper(func):
        def callback(scanner, name, wrapped):
            scanner.config.register_task(wrapped, **kwargs)

        venusian.attach(func, callback, category="pyramid")
        return func

    return wrapper


def _get_task(registry, func_or_name):
    """
    Get task by function or name.

    """
    task_map = registry["pyramid_tasks.task_map"]
    if isinstance(func_or_name, str):
        return _get_app(registry).tasks[func_or_name]
    elif func_or_name in task_map:
        return task_map[func_or_name]
    else:
        raise ValueError("Not a valid task.")


def defer_task(request, func_or_name, *args, **kwargs):
    """
    Add a task to the work queue.  All positional and keyword arguments passed
    into this method will be passed through to the task.  Convenience function
    for ``defer_task_with_options``.

    """
    return defer_task_with_options(
        request,
        func_or_name,
        args=args,
        kwargs=kwargs,
    )


def defer_task_with_options(
    request, func_or_name, args=tuple(), kwargs=None, **options
):
    """
    Add a task to the work queue.  ``func_or_name`` can either by the name of
    the task (str) or the task function itself.  ``args`` and ``kwargs`` will
    be passed into the task.  Additional options will be passed into
    ``Task.apply_async``.  Please refer to Celery documentation to see options.

    """
    kwargs = kwargs if kwargs is not None else dict()
    task = _get_task(request.registry, func_or_name)
    request.registry.notify(
        BeforeDeferTask(
            request=request,
            task=task,
            args=args,
            kwargs=kwargs,
            options=options,
        )
    )
    return task.apply_async(args, kwargs, **options)


def add_periodic_task(
    config, schedule, func_or_name, args=(), kwargs=None, **opts
):
    """
    Add a period task.

    """

    def add():
        task = _get_task(config.registry, func_or_name)
        _get_app(config.registry).add_periodic_task(
            schedule,
            task,
            args,
            kwargs,
            **opts,
        )

    config.action(None, add, order=PHASE3_CONFIG)


def get_task_result(request, task_id):
    """
    Get a result object from celery.

    """
    return _get_app(request.registry).AsyncResult(task_id)


def current_task(request):
    """
    Return the task currently being executed.

    """
    return _get_app(request.registry).current_worker_task


def _connect_worker_process_init(registry):
    """
    Connect a signal handler to Celery's ``worker_process_init`` module.

    """

    def handler(sender=None, **kwargs):
        registry.notify(CeleryWorkerProcessInit(registry))

    signal = celery.signals.worker_process_init
    signal.connect(handler, weak=False)
