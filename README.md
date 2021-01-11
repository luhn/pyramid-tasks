# Pyramid Tasks

Pyramid and Celery are both fantastic projects that compliment each other well:
Pyramid processes synchronous web requests, while Celery performs asynchronous tasks in the background.
Unfortunately, due to differences in structure and configuration, it's very difficult to integrate the two together.
Configuration, clients, etc. available in Pyramid views may be unavailable in tasks, or may need to be accessed in a different way.
Configuration and functionality may have to be duplicated in order to be shared between Pyramid and Celery.
Pyramid Tasks aims to bridge this gap by
**creating a full Pyramid application in the Celery worker and providing a request object to every task.**
You can use the same configuration for Celery that you do Pyramid, including a Paste-style ini file.
Bringing parity to Pyramid and Celery means you can write code for Pyramid and have the code *just work* in Celery.

To see Pyramid Tasks in action, check out the [sample app](https://github.com/luhn/pyramid-tasks/tree/main/examples/basic/).

## Getting Started

To use Pyramid Tasks, you should first be familiar with
[Pyramid](https://docs.pylonsproject.org/projects/pyramid/en/latest/)
and [Celery](https://docs.celeryproject.org/en/stable/).

You can install Pyramid Tasks from PyPI:

```sh
pip install pyramid-tasks
```

Include Pyramid Tasks in your application using `config.include`, or add it to `pyramid.includes` in your ini file.

```sh
config.include('pyramid_tasks')
```

## Configuring Celery

When you import Pyramid Tasks into your application, a new Celery application is created.
All settings prefixed with `celery.` are put into Celery's configuration.
As settings from a .ini file are all strings, values are coerced as necessary.
Nested settings are supported by chaining dots, e.g. `celery.broker_transport_options.queue_name_prefix`.

For example, the following simple `celeryconf.py`:

```python
broker_url = 'redis://'
broker_transport_options = {
    'visibility_timeout': 3600,
}
result_backend = 'redis://'
```

Would be translated into the following .ini file:

```ini
celery.broker_url = redis://
celery.broker_transport_options.visibility_timeout = 3600
celery.result_backend = redis://
```

## Running a Worker

If you're running Pyramid via Paste (i.e. an ini file and possibly `pserve`),
you can run a Celery worker using the same ini file.

```sh
celery -A pyramid_tasks --ini config.ini
```

This will create a Pyramid app via the same process `pserve` does, allowing you to share configuration between the two environments.

You can also create a Celery app using `config.make_celery_app()`, just like you use `config.make_wsgi_app()`.
If you add `app = config.make_celery_app()` to `celery.py` in your project's package, you can invoke `celery -A myproject worker` to boot a worker.

To see both methods of running a worker in action, take a look at the [sample app](https://github.com/luhn/pyramid-tasks/tree/main/examples/basic/).

## Registering Tasks

To register a new task, call `config.register_task` with the task function.
You can also use the `pyramid_tasks.task` decorator as long as you run a scan (`config.scan()`) on the package, just like Pyramid's `view_config` decorator.
`register_task` and `@task` take the same arguments as [Celery.task](https://docs.celeryproject.org/en/stable/reference/celery.html#celery.Celery.task).

For example, a simple Pyramid app with a task might look like the following:

```python
from pyramid.config import Configurator


def add(request, x, y):
    return x + y


with Configurator() as config:
    config.register_task(add, name='add')
```

## Invoking a Task

Once a task is registered, you can add it to the work queue using `request.delay_task`.
This takes the task function or a string of the name of the task as the first argument.
The remaining arguments (positional and keywork) will be passed to the task.
When the task is invoked by a Celery worker, a request object will be created and passed as the first argument.

This request object will share the same configuration as requests in the Pyramid application.
This means it will have the same or similar methods, registry, etc.
However, it is not *the* request that invoked the task and properties such as `url`, `GET`, etc. will not be present.
To use these values in your task, pass them in as arguments.

Let's take our simple Pyramid app and add a view that invokes the task.


```python
from pyramid.config import Configurator


def add_view(context, request):
    request.delay_task(add, int(request.GET['x']), int(request.GET['y']))
    return 'OK\n'


def add(request, x, y):
    return x + y


with Configurator() as config:
    config.add_route('root', '/')
    config.add_view(add_view, route_name='root')
    config.register_task(add, name='add')
```

## Getting Task Results

`request.delay_task` returns a Celery [AsyncResult](https://docs.celeryproject.org/en/stable/reference/celery.app.task.html#celery.app.task.Task.AsyncResult) object.
You can use this object to check if the task has completed (`AsyncResult.ready()`) and to get the return value of the task (`AsyncResult.result`).
See the Celery docs for more information.

`AsyncResult` also has an `id` property.
If you store this property somewhere, such as a client session, you can use `request.get_task_result(id)` to return a new `AsyncResult` object.

## Tweens

Pyramid has a feature called [tweens](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#registering-tweens)
that lets developers add middleware to the request pipeline, which can be used for transaction management, performance monitoring, error handling, and much more.
Pyramid Task has an analog to this feature called "task tweens."

Task tweens operate in much the same way as tweens.
A tween factory, given a task function and the application registry, returns a function.
For example, here's the code used to inject a request as the first argument:

```python
def request_tween_factory(handler, registry):
    def tween(*args, **kwargs):
        with prepare(registry=registry) as env:
            return handler(env["request"], *args, **kwargs)

    return tween
```

Register a tween by calling `Configurator.add_task_tween` with a Zope-style dotted name for your factory function.

```python
config.add_task_tween('myproject.tweens.my_tween_factory')
```

You can also specify the ordering of task tweens by using `over` and/or `under` arguments, just like Pyramid tweens.
A tween "over" another tween means it is executed earlier in the pipeline.
The special attribute `pyramid_tasks.tweens.INGRESS` represents the top of the stack, `pyramid_tasks.tweens.MAIN` represents the bottom (i.e. the task itself).
`pyramid_tasks.tweens.REQUEST_TWEEN` is a built-in tween that creates a request object and injects it as the first argument.
Any tween that depends on a request object should be placed under `REQUEST_TWEEN`.

```python
config.add_task_tween('myproject.tweens.my_tween_factory')
config.add_task_tween(
    'myproject.tweens.another_factory',
    over='myproject.tweens.my_tween_factory',
    under=REQUEST_TWEEN,
)
```

## pyramid_tm Integration

[pyramid_tm](https://docs.pylonsproject.org/projects/pyramid-tm/en/latest/) is the recommended way of adding transaction management to Pyramid.
For example, the [Pyramid cookiecutter](https://github.com/Pylons/pyramid-cookiecutter-starter)
uses `pyramid_tm` and `zope.sqlalchemy` to integrate SQLAlchemy into Pyramid.

Pyramid Tasks includes built-in support for pyramid_tm.
It can be enabled by including `pyramid_tasks.transaction` in your project.
This must be included after Pyramid Tasks, but doesn't need to be included before pyramid_tm.

To see Pyramid Tasks, pyramid_tm, and SQLAlchemy in action, check out the [SQLAlchemy sample app](https://github.com/luhn/pyramid-tasks/tree/main/examples/sqlalchemy).

## Periodic Tasks

Pyramid Tasks supports [Celery Beat](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html) for running periodic tasks.
After registering a task, use `config.add_periodic_task` to schedule the task.
The arguments mirror [Celery.add_periodic_task](https://docs.celeryproject.org/en/stable/reference/celery.html#celery.Celery.add_periodic_task):

```python
config.add_periodic_task(
    5.0,  # Run every five seconds
    'mytask',
    ('foo', 'bar'),  # Position arguments passed to task
    {'fizz': 'buzz'},  # Keyword arguments passed to task
)
```

You can also use [celery.schedules.crontab](https://docs.celeryproject.org/en/stable/reference/celery.schedules.html#celery.schedules.crontab)
as the first argument to use crontab-style scheduling.

You can run the Beat scheduler the same way you run the Celery worker.

```sh
celery -A pyramid_tasks beat --ini config.ini
```

To see Celery Beat in action, check out the [beat sample app](https://github.com/luhn/pyramid-tasks/tree/main/examples/beat/).

## Acknowledgements

Pyramid Tasks is heavily inspired by the code of PyPA's [Warehouse](https://github.com/pypa/warehouse/) project.
