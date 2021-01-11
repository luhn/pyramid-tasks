# Pyramid Tasks Sample App

This app stores an append-only ledger in SQLite and totals the ledger values in a task.
We use SQLAlchemy as a ORM and query builder, integrated into Pyramid with
[zope.sqlalchemy](https://pypi.org/project/zope.sqlalchemy/)
and [pyramid_tm](https://docs.pylonsproject.org/projects/pyramid-tm/en/latest/)
as laid out by Pyramid's
[SQLAlchemy + URL Dispatch Wiki Tutorial](https://docs.pylonsproject.org/projects/pyramid/en/latest/tutorials/wiki2/).

For instructions on how to run, see the [basic example README](https://github.com/luhn/pyramid-tasks/blob/main/examples/basic/README.md#running-locally).

## Tour of the Code

We won't dive too deeply into the code, because it's largely based off of
Pyramid's [SQLAlchemy + URL Dispatch Wiki Tutorial](https://docs.pylonsproject.org/projects/pyramid/en/latest/tutorials/wiki2/)
and implements similar functionality as the [basic sample app](../basic/).
We'll quickly highlight how we integrate the SQLAlchemy into Pyramid Task.

First let's take a look at `sqlalchemyapp/models/__init__.py` to review how SQLAlchemy is integrated into the Pyramid app.

Our code adds a `db` property to the request object, which provides us with a SQLAlchemy session to use.

```python
config.add_request_method(
		lambda request: get_tm_session(session_factory, request.tm),
		"db",
		reify=True,
)
```

We then include `pyramid_tm` to manage opening and closing our transactions.
The explicit transaction manager is highly recommneded, so we configure that.

```python
config.add_settings(
		{
				"tm.manager_hook": "pyramid_tm.explicit_manager",
		}
)
config.include("pyramid_tm")
```

Now let's hop over to `sqlalchemyapp/tasks.py` and take a look at our task.

```python
def total_task(request):
    return request.db.query(func.sum(Ledger.amount)).scalar() or 0
```

Thanks to Pyramid Task, we automatically have use of our `db` property without any additional configuration.
However, since `pyramid_tm` relies on [tweens](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/hooks.html#registering-tweens),
which aren't executed for tasks, transaction management will not work properly out of the box.

We rectify this by including Pyramid Task's built-in pyramid_tm support.
This module configures a simple task tween (Pyramid Task's analog to Pyramid tweens) that wraps every task in a transaction.

```python
config.include("pyramid_tasks")
config.include("pyramid_tasks.transaction")
```

That's all.  One extra line and you have working transactions in your tasks.
