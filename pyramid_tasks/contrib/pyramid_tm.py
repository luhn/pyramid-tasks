"""
Emulates ``pyramid_tm`` functionality inside of Celery.

"""


def includeme(config):
    config.add_task_deriver(transaction_task_deriver)


def transaction_task_deriver(task, info):
    def deriver(request, *args, **kwargs):
        environ = request.environ
        if environ.get("tm.active"):
            return task(request, *args, **kwargs)

        manager = request.tm
        environ["tm.active"] = True
        environ["tm.manager"] = manager

        with manager:
            return task(request, *args, **kwargs)

    return deriver
