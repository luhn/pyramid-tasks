"""
Implementation of task tweens, an analog of Pyramid's tweens.

Because of the overlap in functionality, the code maps closely to Pyramid's
implementation.

"""
from pyramid.interfaces import PHASE0_CONFIG
from pyramid.scripting import prepare
from pyramid.util import TopologicalSorter
from zope.interface import Interface, implementer

REQUEST_TWEEN = "pyramid_tasks.tweens.request_tween_factory"


class ITaskTweens(Interface):
    """
    Marker for utility providing ordered tweens.

    """

    pass


@implementer(ITaskTweens)
class TaskTweens:
    def __init__(self):
        self.sorter = TopologicalSorter()

    def add(self, name, factory, under=None, over=None):
        self.sorter.add(name, factory, after=under, before=over)

    def __call__(self, handler, registry):
        tweens = self.sorter.sorted()
        for name, factory in reversed(tweens):
            handler = factory(handler, registry)
        return handler


def add_task_tween(config, name, under=None, over=None):
    if not isinstance(name, str):
        raise ValueError("Name must be a string.")
    factory = config.maybe_dotted(name)

    registry = config.registry
    tweens = registry.queryUtility(ITaskTweens)
    if tweens is None:
        tweens = TaskTweens()
        registry.registerUtility(tweens, ITaskTweens)

    def add():
        tweens.add(name, factory, under=under, over=over)

    discriminator = ("task tween", name)
    config.action(discriminator, add, order=PHASE0_CONFIG)


def request_tween_factory(handler, registry):
    """
    A tween that creates a request and appends it to the task arguments

    """

    def tween(*args, **kwargs):
        with prepare(registry=registry) as env:
            return handler(env["request"], *args, **kwargs)

    return tween
