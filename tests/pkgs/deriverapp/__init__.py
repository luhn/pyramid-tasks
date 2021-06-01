def includeme(config):
    config.registry["db"] = MockDatabase()
    config.add_request_method(
        lambda req: req.registry["db"],
        name="db",
        reify=True,
    )
    config.add_task_deriver(transaction_task_deriver)
    config.register_task(increment_task, name="increment", in_transaction=True)


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


def transaction_task_deriver(task, info):
    if not info.options.get("in_transaction", False):
        return task

    def derived(request, *args, **kwargs):
        with request.db:
            return task(request, *args, **kwargs)

    return derived


def increment_task(request, x=1):
    count = request.db["counter"] or 0
    request.db["counter"] = count + x
    return request.db["counter"]
