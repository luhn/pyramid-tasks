"""
Support for transaction/pyramid_tm.

"""


def includeme(config):
    config.add_task_deriver(transaction_task_deriver)


def transaction_task_deriver(task, info):
    def deriver(request, *args, **kwargs):
        with request.tm:
            return task(request, *args, **kwargs)

    return deriver
