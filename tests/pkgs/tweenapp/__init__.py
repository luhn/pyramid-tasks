from zope.interface import Interface

from pyramid_tasks.tweens import REQUEST_TWEEN


def includeme(config):
    config.registry.registerUtility(MockDatabase(), IDatabase)
    config.add_request_method(
        lambda req: req.registry.queryUtility(IDatabase),
        name="db",
        reify=True,
    )
    config.add_task_tween(
        "tests.pkgs.tweenapp.transaction_tween_factory", under=REQUEST_TWEEN
    )
    config.register_task(increment_task, name="increment")


class IDatabase(Interface):
    pass


class MockDatabase:
    """
    A simple database.

    """

    def __init__(self):
        self._store = dict()
        self._open = False

    def __enter__(self):
        if self._open:
            raise RuntimeError("Transaction already open.")
        self._open = True

    def __exit__(self, type, value, traceback):
        if not self._open:
            raise RuntimeError("No transaction open.")
        self._open = False

    @property
    def is_open(self):
        return self._open

    def __getitem__(self, key):
        if not self._open:
            raise RuntimeError("No transaction open.")
        return self._store.get(key)

    def __setitem__(self, key, value):
        if not self._open:
            raise RuntimeError("No transaction open.")
        self._store[key] = value


def transaction_tween_factory(handler, registry):
    def tween(request, *args, **kwargs):
        with request.db:
            return handler(request, *args, **kwargs)

    return tween


def increment_task(request, x=1):
    count = request.db["counter"] or 0
    request.db["counter"] = count + x
    return request.db["counter"]
