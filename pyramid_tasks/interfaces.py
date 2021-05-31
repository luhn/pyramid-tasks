from zope.interface import Attribute, Interface


class ITaskDeriver(Interface):
    def __call__(task, info):
        """
        Derive a new task from the supplied task.

        View options, package information and registry are available on
        ``info``, an instance of
        :class:`pyramid_tasks.interfaces.ITaskDeriverInfo`.

        The ``task`` is a callable accepting ``(request, *args, **kwargs)``.

        """


class ITaskDeriverInfo(Interface):
    """
    An object implementing this interface is passed to every task deriver
    during configuration.

    """

    registry = Attribute(
        'The "current" application registry where the task was created'
    )
    package = Attribute(
        "The current package where the configuration statement was found"
    )
    name = Attribute("The name of the task.")
    options = Attribute("The options passed to the task.")
    original_func = Attribute(
        "The original function being transformed into a task."
    )


class ITaskDerivers(Interface):
    """Interface for task derivers list."""

    def add(self, name, factory, after=None, before=None):
        """
        Add a task deriver to the list.

        """

    def sorted(self):
        """
        Return a sorted list of task derivers.

        """
