"""
Task derivers are the task analog of Pyramid's view derivers.

"""
from pyramid.interfaces import PHASE0_CONFIG
from pyramid.util import TopologicalSorter

from .interfaces import ITaskDerivers


def includeme(config):
    config.registry.registerUtility(TopologicalSorter(), ITaskDerivers)
    config.add_directive(
        "add_task_deriver", add_task_deriver, action_wrap=True
    )


def add_task_deriver(config, deriver, name=None, under=None, over=None):
    """
    Add a task deriver to the list.

    """
    deriver = config.maybe_dotted(deriver)

    if name is None:
        name = deriver.__name__

    discriminator = ("task deriver", name)
    intr = config.introspectable("task derivers", name, name, "task deriver")
    intr["name"] = name
    intr["deriver"] = deriver
    intr["under"] = under
    intr["over"] = over

    derivers = config.registry.getUtility(ITaskDerivers)

    def add():
        derivers.add(name, deriver, after=under, before=over)

    config.action(discriminator, add, order=PHASE0_CONFIG)


def apply_task_derivers(config, task, name, options):
    """
    Apply the task derivers to a task.

    """
    derivers = config.registry.getUtility(ITaskDerivers).sorted()
    info = TaskDeriverInfo(
        registry=config.registry,
        package=config.package,
        name=name,
        options=options,
        original_func=task,
    )
    for name, deriver in reversed(derivers):
        task = deriver(task, info)
    return task


class TaskDeriverInfo:
    def __init__(self, registry, package, name, options, original_func):
        self.registry = registry
        self.package = package
        self.name = name
        self.options = options
        self.original_func = original_func
