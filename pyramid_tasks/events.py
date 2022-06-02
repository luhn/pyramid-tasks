class BeforeDeferTask:
    """
    This event is emitted before a task is queued (``Task.apply_async()``).

    The ``kwargs`` attribute is a dictionary containing the keyword arguments
    to be passed into ``Task.apply_async``.  Modifying this dictionary will
    modify the keywords arguments passed.

    """

    def __init__(self, request, task, args, kwargs, options):
        self.request = request
        """The current request."""
        self.task = task
        """The task being queued."""
        self.task_name = task.name
        """The name of the task being queued."""
        self.args = args
        """The position arguments the task will be invoked with."""
        self.kwargs = kwargs
        """The keyword arguments the task will be invoked with."""
        self.options = options
        """The additional options being passed in to ``Task.apply_async``."""


class CeleryWorkerProcessInit:
    """
    This is event is emitted Celery's ``worker_process_init`` signal.  Useful
    for disposing of any multiprocess unsafe resources.

    See more:  https://docs.celeryq.dev/en/stable/userguide/signals.html

    """

    def __init__(self, registry):
        self.registry = registry
        """The current Pyramid registry."""
