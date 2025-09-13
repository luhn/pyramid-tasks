"""
For backwards compatibility.  For new proejcts, use
``pyramid_tasks.contrib.pyramid_tm`` instead.

"""

from .contrib.pyramid_tm import transaction_task_deriver


def includeme(config):
    config.include(".contrib.pyramid_tm")


__all__ = [
    "transaction_task_deriver",
]
