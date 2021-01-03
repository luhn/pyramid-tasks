# Pyramid Task Sample App

This app stores an append-only ledger and totals the ledger values in a task.

## A Tour of the Code

The bulk of the functionality is located at [sampleapp/__init__.py](sampleapp/__init__.py).
Here's a quick overview of the functions in the file:

- `configure` — Create the Pyramid app.
- `application` — Return a WSGI app, for running with Paste/pserve.
- `configure_redis` — Configure the Pyramid app to add a `redis` property to `request`.
- `append` — A view that appends a value to the ledger.
- `total` — A view that queues a task to total the ledger.
- `result` — A view that looks up the result of a task.
- `total_task` — The Celery task that totals the ledger.

First let's look at `configure`.
For the most part it's standard Pyramid configuration, adding routes and views.
We'll skip over the boring parts, but I want to highlight a few lines.

We set the `celery.broker_url` and `celery.result_backend` settings if not already set.
Pyramid Task will extract these from the Pyramid settings and set `broker_url` and `result_backend` in the Celery config.
This is how we tell Celery to use Redis for the broker and backend.

```python
settings.setdefault("celery.broker_url", redis_url)
settings.setdefault("celery.result_backend", redis_url)
```

We of course need to include Pyramid Task into the celery config.

```python
config.include("pyramid_tasks")
```

And lastly, we need to register our task with Celery.

```python
config.register_task(total_task)
```

That's it.
This `configure` function gives us a Pyramid app with a Celery worker, with just a few extra lines of configuration.

Now let's dive into our application logic, starting with the `append` view.

```python
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
```

This function doesn't interact with Celery at all, but I want to point out `request.redis.rpush`.
Our `configure_redis` function adds a `redis` property to the request object, which contains a Redis client.
You'll see more of `request.redis` later on.

Let's move on to some code that interacts with Celery.  Take a look at the `total` view.

```python
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
```

You can see we call `request.delay_task`, which puts `total_task` onto the Celery queue.
The Celery worker will pick this up and run the `total_task` function asynchronously.
Remember that we registered `total_task` in the configuration, so that Celery is aware of it.

`request.delay_task` returns a [celery.result.AsyncResult](https://docs.celeryproject.org/en/stable/reference/celery.result.html#celery.result.AsyncResult) object.
We return the `id` property to the user so we can reference the task again later.

Let's look at this `total_task` function Celery is running.

```python
def total_task(request, delay=0.0):
    """
    A task to total the ledger.

    """
    sleep(delay)
    values = request.redis.lrange("ledger", 0, -1)
    return sum((int(val.decode("ascii")) for val in values), 0)
```

You'll see the first argument is `request`, which is added by Pyramid Task.
This is a request just like the one used by our Pyramid app, pulling from the same configuration.
With no extra code or wrangling of Celery, we can use `request.redis` in our task.
This is the magic of Pyramid Task:  You can write your task code in the same way you write your view code.

It's worth noting that althugh `request ` is a request object, it's not the same request object that queued the task.
If you inspect `request.url` or `request.GET`, you'll find them quite empty.
To get these values into your task, pass them as arguments.

Now let's turn to the result view:

```python
def result(context, request):
    """
    Get result of the task.

    """
    result = request.get_task_result(request.GET["id"])
    if result.ready():
        return f"{ result.result }\n"
    else:
        return "Pending...\n"
```

Here we're taking the `id` we returned earlier and passing it into `request.get_task_result`.
This returns a `celery.result.AsyncResult` object, just like `request.delay_task` did.
We take the `AsyncResult` and make sure the task has completed (`result.ready()`).
If it has, we return the task's output (`result.result`).

There we have it.  A fully functional Pyramid application with a Celery worker.

There are a couple other files in the `sampleapp` package that I'll briefly touch on.

`sampleapp/__main__.py` boots a simple WSGI server on port 8000.

`sampleapp/celery.py` runs `app = configure().make_celery_app()`, which sets `app` to the Celery application created by Pyramid Task.
When you run `celery -A sampleapp worker`, Celery will find `app` and use it in the worker.

If you're using `pserve` to run your application, these two files are not required.

## Running in Docker

If you want to see the sample app in action, the easiest way is to run in Docker with `docker-compose up`.
This will launch the app on port 8000, a Celery worker, and Redis.

## Running Locally

This sample app requires Redis, so install and run Redis on your machine.

First, install the app and its dependencies:

```sh
pip install .
```

Run the app:

```sh
python -m sampleapp
```

In a different terminal, run the Celery worker:

```sh
celery -A sampleapp worker -l INFO
```

By default, the app will look for Redis on localhost port 6379.
To point it elsewhere, set the `REDIS_URL` environment variable when running the app and the worker.

```sh
REDIS_URL=redis://host:123 python -m sampleapp
REDIS_URL=redis://host:123 celery -A sampleapp worker -l INFO
```

### Paste/pserve

TODO

## Using

```
>>> # Add a value to the ledger
>>> curl http://localhost:8000/append\?value=10
Done.
>>> # Start the totaling task with a 5 second delay.
>>> curl localhost:8000/total\?delay=5
c7f6a7c5-897b-4c01-89b4-e1cc3f2a30d5
>>> # Get the result, using the UUID from the previous command.
>>> curl localhost:8000/result\?id=c7f6a7c5-897b-4c01-89b4-e1cc3f2a30d5
10
```
