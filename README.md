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

Is equivalent to the following .ini file:

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

Once a task is registered, you can add it to the work queue using `request.defer_task`.
This takes the task function or a string of the name of the task as the first argument.
The remaining arguments (positional and keyword) will be passed to the task.
When the task is invoked by a Celery worker, a request object will be created and passed as the first argument.

This request object will share the same configuration as requests in the Pyramid application.
This means it will have the same or similar methods, registry, etc.
However, it is not *the* request that invoked the task and properties such as `url`, `GET`, etc. will not be present.
To use these values in your task, pass them in as arguments.

Let's take our simple Pyramid app and add a view that invokes the task.


```python
from pyramid.config import Configurator


def add_view(context, request):
    request.defer_task(add, int(request.GET['x']), int(request.GET['y']))
    return 'OK\n'


def add(request, x, y):
    return x + y


with Configurator() as config:
    config.add_route('root', '/')
    config.add_view(add_view, route_name='root')
    config.register_task(add, name='add')
```

You can also use `request.defer_task_with_options` to pass options into Celery.
See the [Celery docs](https://docs.celeryproject.org/en/stable/reference/celery.app.task.html#celery.app.task.Task.apply_async) for details on what options are available.
For example:

```python
def add_view(context, request):
    args = int(request.GET['x']), int(request.GET['y'])
    request.defer_task_with_options(add, args=args, countdown=5)
    return 'OK\n'
```


## Getting Task Results

`request.defer_task` returns a Celery [AsyncResult](https://docs.celeryproject.org/en/stable/_modules/celery/result.html#AsyncResult) object.
You can use this object to check if the task has completed (`AsyncResult.ready()`) and to get the return value of the task (`AsyncResult.result`).
See the Celery docs for more information.

`AsyncResult` also has an `id` property.
If you store this property somewhere, such as a client session, you can use `request.get_task_result(id)` to return a new `AsyncResult` object.

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

## Extending Tasks:  Task Derivers

Task Derivers are analogous to Pyramid's [View Derivers](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#view-derivers).
They allow you to transform the task before registering it, such as wrapping the task in a transaction or adding metric collection.

A task deriver is a callable that takes two arguments:  A task function and an info object.
The deriver should return a task callable.
The info object has the following attributes:

* `registry` — The registry for the current Pyramid application.
* `package` — The package where the configuration statement was found.
* `name` — The name of the task.
* `options` — The options passed in to the register task action.
* `original_func` — The original task function.

You can register a new task deriver with the `Configurator.add_task_deriver` method.
The first argument is the task deriver.
The second argument is the name.
If omitted, the name of the task deriver function will be used.
It also optionally takes `over` and `under` arguments, which work the same as with Pyramid's view deriver.

For example, here's a simple task deriver that wraps the task in a database transaction:

```python
def transaction_deriver(task, info):
    def wrapped(request, *args, **kwargs):
        with request.db:
            task(request, *args, **kwargs)

    return wrapped

def includeme(config):
    config.add_task_deriver(transaction_deriver)
```

You can pass in options when registering the task to configure your task derivers.
For example, here's the same transaction task deriver as above, but now will only wrap the task if the `in_transaction` option is set.

```python
def transaction_deriver(task, info):
    def wrapped(request, *args, **kwargs):
        with request.db:
            task(request, *args, **kwargs)

    if info.options.get('in_transaction', False):
		    return wrapped
    else:
        return task
```

Celery will accept any keyword arguments passed in, so no configuration is necessary to use your own options.
All options will be set as attributes on the task object.

## Extending Tasks:  Events

Pyramid Task also fires events using Pyramid's [event system](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/events.html).
Currently the only event is `pyramid_task.events.BeforeDeferTask`, which will fire when calling `defer_task` or `defer_task_with_options`.
The event contains the following attributes:

* `request` — The current request.
* `task` — The task being deferred.
* `args` — The arguments being passed to the task.
* `kwargs` — The keyword arguments being passed to the task.
* `options` — The options being passed into `Task.apply_async`.

You can modify `options` in-place and the changes will be reflected in the `apply_async` call.

For example, here's an event subscriber that adds the current user ID to the headers.

```python
def add_headers(event):
    headers = event.options.setdefault('headers', {})
    headers.setdefault('user_id', event.request.authenticated_userid)

def includeme(config):
    config.add_subscriber(add_headers, BeforeDeferTask)
```

The user ID will now be accessible from `request.current_task.request.user_id`.

## Fork Safety

Celery by default uses a pre-fork worker model,
meaning the application will be initialized and then forked to launch the desired number of workers.
This can cause issues with some libraries, especially ones utilizing file descriptors such as database connections.
For example, [SQLAlchemy requires disposing connections on fork](https://docs.sqlalchemy.org/en/14/core/pooling.html#using-connection-pools-with-multiprocessing-or-os-fork).
You can do this by subscribing to the `pyramid_task.events.CeleryWorkerProcessInit` event.

``python
config.add_subscriber(lambda _: engine.pool.recreate(), CeleryWorkerProcessInit)
```

The event includes the current [application registry](https://docs.pylonsproject.org/projects/pyramid/en/2.0-branch/api/registry.html) in the `registry` property.

`CeleryWorkerProcessInit` is triggered by Celery's `worker_process_init` signal, so use it in the same situations you would that signal.

## Acknowledgements

Pyramid Tasks is heavily inspired by the code of PyPA's [Warehouse](https://github.com/pypa/warehouse/) project.
