class BeforeTaskApply:
    """
    This event is emitted before a task is queued (``Task.apply_async()``).

    The ``kwargs`` attribute is a dictionary containing the keyword arguments
    to be passed into ``Task.apply_async``.  Modifying this dictionary will
    modify the keywords arguments passed.

    """

    def __init__(self, request, task, kwargs):
        self.request = request
        """The current request."""
        self.task = task
        """The task being queued."""
        self.task_name = task.name
        """The name of the task being queued."""
        self.kwargs = kwargs
        """The keyword arguments being passed in to ``Task.apply_async``."""
