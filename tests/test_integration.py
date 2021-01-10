from contextlib import contextmanager
from unittest.mock import Mock

import pytest
from celery.contrib.testing.worker import start_worker
from pyramid.scripting import prepare
from pyramid.testing import testConfig as _testConfig


@pytest.fixture
def test_config():
    settings = {
        "celery.worker_hijack_root_logger": False,
        "celery.worker_log_color": False,
        "celery.accept_content": "json",
        "celery.enable_utc": True,
        "celery.timezone": "UTC",
        "celery.broker_url": "memory://",
        "celery.result_backend": "cache+memory://",
        "celery.broker_heartbeat": 0,
    }
    with _testConfig(settings=settings, autocommit=False) as config:
        config.include("pyramid_tasks")
        yield config


@contextmanager
def make_request_with_worker(config):
    config.commit()
    with prepare(registry=config.registry) as env:
        with make_worker(config):
            yield env["request"]


@contextmanager
def make_worker(config):
    with start_worker(config.make_celery_app(), perform_ping_check=False):
        yield None


def test_simple_integration(test_config):
    def add_task(request, x, y):
        return x + y

    test_config.register_task(add_task, name="add")
    with make_request_with_worker(test_config) as request:
        result = request.delay_task("add", 2, 3)
    assert result.get() == 5


def test_task_by_function_integration(test_config):
    def add_task(request, x, y):
        return x + y

    test_config.register_task(add_task, name="add")
    with make_request_with_worker(test_config) as request:
        result = request.delay_task(add_task, 2, 3)
    assert result.get() == 5


def test_task_venusian_integration(test_config):
    test_config.include("tests.pkgs.venusianapp")
    with make_request_with_worker(test_config) as request:
        result = request.delay_task("venusian_add_task", 2, 3)
    assert result.get() == 5


def test_get_task_result_integration(test_config):
    def add_task(request, x, y):
        return x + y

    test_config.register_task(add_task, name="add")
    with make_request_with_worker(test_config) as request:
        task_id = request.delay_task("add", 2, 3).id
        result = request.get_task_result(task_id)
    assert result.get() == 5


def test_task_request_argument_integration(test_config):
    task = Mock(return_value=None)
    test_config.register_task(task, name="test")
    app = test_config.make_celery_app()
    with make_worker(test_config):
        app.tasks["test"].apply_async().get()
    request = task.call_args[0][0]
    assert request.registry == test_config.registry


def test_task_tween_integration(test_config):
    from tests.pkgs.tweenapp import IDatabase

    test_config.include("tests.pkgs.tweenapp")

    db = test_config.registry.queryUtility(IDatabase)
    with db:
        db["counter"] = 3

    app = test_config.make_celery_app()
    with make_worker(test_config):
        assert app.tasks["increment"].apply_async((4,)).get() == 7
