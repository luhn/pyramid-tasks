from unittest.mock import Mock

from pyramid.config import Configurator
from pyramid.registry import Registry

from pyramid_tasks.tweens import (
    ITaskTweens,
    TaskTweens,
    add_task_tween,
    request_tween_factory,
)


def test_task_tweens_call():
    handler = Mock(return_value="a")

    def b_factory(handler, registry):
        def tween(*args, **kwargs):
            return "b" + handler("b", *args, **kwargs)

        return tween

    def c_factory(handler, registry):
        def tween(*args, **kwargs):
            return registry["c"] + handler("c", *args, **kwargs)

        return tween

    tweens = TaskTweens()
    tweens.add("b", b_factory)
    tweens.add("c", c_factory, over="b")
    result = tweens(handler, {"c": "see"})
    assert result("d") == "seeba"
    handler.assert_called_once_with("b", "c", "d")


def _test_tween_a(hander, registry):
    pass


def _test_tween_b(hander, registry):
    pass


def test_add_task_tween():
    class MockTweens(set):
        def add(self, name, factory, under=None, over=None):
            super().add(
                (name, factory, under, over),
            )

    tweens = MockTweens()
    config = Configurator()
    config.registry.registerUtility(tweens, ITaskTweens)
    add_task_tween(config, "tests.test_tweens._test_tween_a")
    add_task_tween(
        config,
        "tests.test_tweens._test_tween_b",
        under="tests.test_tweens._test_tween_a",
        over="MAIN",
    )
    config.commit()
    assert tweens == {
        ("tests.test_tweens._test_tween_a", _test_tween_a, None, None),
        (
            "tests.test_tweens._test_tween_b",
            _test_tween_b,
            "tests.test_tweens._test_tween_a",
            "MAIN",
        ),
    }


def test_request_tween_factory():
    registry = Registry()
    handler = Mock(return_value="abc")
    result = request_tween_factory(handler, registry)
    assert result("foo", fizz="buzz") == "abc"
    args, kwargs = handler.call_args
    assert args[1:] == ("foo",)
    assert kwargs == {"fizz": "buzz"}
    request = args[0]
    assert request.registry == registry
