"""
Support for transaction/pyramid_tm.

"""
from .tweens import REQUEST_TWEEN


def includeme(config):
    config.add_task_tween(
        "pyramid_tasks.transaction.transaction_tween", under=REQUEST_TWEEN
    )


def transaction_tween(handler, registry):
    def tween(request, *args, **kwargs):
        with request.tm:
            return handler(request, *args, **kwargs)

    return tween
