from unittest.mock import MagicMock

import pytest
from pyramid.testing import DummyRequest

from pyramid_tasks.contrib.pyramid_tm import transaction_task_deriver


class TestTransactionTastDeriver:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.request = DummyRequest()
        self.tm = MagicMock()
        self.request.tm = self.tm
        self.task = MagicMock()

    def call(self, task, info=None):
        return transaction_task_deriver(task, info)

    def call_wrapped(self, *args, **kwargs):
        wrapped = self.call(self.task)
        return wrapped(self.request, *args, **kwargs)

    def test_calls_handler_with_args(self):
        self.call_wrapped(1, 2, foo="bar")
        self.task.assert_called_once_with(self.request, 1, 2, foo="bar")

        assert self.request.environ["tm.active"]
        assert self.request.environ["tm.manager"] == self.tm
        self.tm.__enter__.assert_called_once_with()
        self.tm.__exit__.assert_called_once_with(None, None, None)

    def test_skips_if_active(self):
        self.request.environ["tm.active"] = True
        self.call_wrapped(1, 2, foo="bar")
        self.task.assert_called_once_with(self.request, 1, 2, foo="bar")

        self.tm.__enter__.assert_not_called()
