from pyramid_tasks.settings import extract_celery_settings


def test_extract_settings_basic():
    settings = {
        "celery.foo": "bar",
        "celery.fizz": "buzz",
    }
    assert extract_celery_settings(settings) == {
        "foo": "bar",
        "fizz": "buzz",
    }


def test_extract_settings_bool():
    settings = {
        "celery.task_acks_late": "yes",
        "celery.task_ignore_result": False,
    }
    assert extract_celery_settings(settings) == {
        "task_acks_late": True,
        "task_ignore_result": False,
    }


def test_extract_settings_int():
    settings = {
        "celery.worker_concurrency": "3",
    }
    assert extract_celery_settings(settings) == {
        "worker_concurrency": 3,
    }


def test_extract_settings_float():
    settings = {
        "celery.task_soft_time_limit": "1.5",
        "celery.task_time_limit": "3",
    }
    assert extract_celery_settings(settings) == {
        "task_soft_time_limit": 1.5,
        "task_time_limit": 3.0,
    }


def test_extract_settings_list():
    settings = {
        "celery.result_accept_content": "json, pickle",
    }
    assert extract_celery_settings(settings) == {
        "result_accept_content": ["json", "pickle"],
    }


def test_extract_settings_dict():
    settings = {
        "celery.broker_transport_options.max_retries": "3",  # int coercion
        "celery.broker_transport_options.foo.fizz": "buzz",
        "celery.broker_transport_options.bar": "baz",
    }
    assert extract_celery_settings(settings) == {
        "broker_transport_options": {
            "max_retries": 3,
            "bar": "baz",
            "foo": {
                "fizz": "buzz",
            },
        },
    }
