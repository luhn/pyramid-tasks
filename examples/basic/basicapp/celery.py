"""
Make the Celery application.  This is in a separate module so that it doesn't
get executed when trying to run the WSGI app.

Run a celery worker with `celery -A sampleapp`

"""
from . import configure

app = configure().make_celery_app()
