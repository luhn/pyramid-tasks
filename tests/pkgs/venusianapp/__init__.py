"""
Test adding a task via venusian.

"""
from pyramid_tasks import task


def includeme(config):
    config.scan(".")


@task(name="venusian_add_task")
def add_task(request, x, y):
    return x + y
