# Periodic Tasks Sample

An app showing the integration between Pyramid Tasks and [Celery Beat](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html).
The app prints "PING" on the worker every five seconds.

The code is very simple.
We define a `print_message` function that prints a message.

```python
def print_message(request, message):
    print(message)
```

In our config, we register the `print_message` task and set it to run every 5 seconds with "PING" as the first argument.

```python
config.register_task(print_message)
config.add_periodic_task(5.0, print_message, ("PING",))
```

## Running in Docker

If you want to see the app in action, easiest way is with Docker Compose.

```sh
docker-compose up
```

## Running Locally

Make sure Redis is installed and running on your machine.

Install the app:

```sh
pip install .
```

Launch the Celery worker:

```sh
celery -A beatapp worker
```

Launch the Beat worker:

```sh
celery -A beatapp beat
```

You should see "PING" print in the worker every five seconds.

### Running with Paste

Launch the worker:

```sh
celery -A pyramid_tasks worker --ini config.ini
```

Launch the Beat worker:

```sh
celery -A pyramid_tasks beat --ini config.ini
```

