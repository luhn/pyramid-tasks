import os

import zope.sqlalchemy
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from pyramid_tasks.events import CeleryWorkerProcessInit

from .ledger import Ledger
from .meta import Base

__all__ = ["Ledger"]


def get_engine(settings, prefix="sqlalchemy."):
    return engine_from_config(settings, prefix)


def get_session_factory(engine):
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory


def get_tm_session(session_factory, transaction_manager):
    dbsession = session_factory()
    zope.sqlalchemy.register(
        dbsession, transaction_manager=transaction_manager
    )
    return dbsession


def includeme(config):
    config.add_settings(
        {
            "tm.manager_hook": "pyramid_tm.explicit_manager",
        }
    )
    config.include("pyramid_tm")

    settings = config.get_settings()
    if "sqlalchemy.url" not in settings:
        sqlalchemy_url = os.environ.get(
            "SQLALCHEMY_URL", "sqlite:///database.db"
        )
        config.add_settings(
            {
                "sqlalchemy.url": sqlalchemy_url,
            }
        )

    dbengine = get_engine(config.get_settings())
    Base.metadata.create_all(bind=dbengine)

    session_factory = get_session_factory(dbengine)
    config.registry["dbsession_factory"] = session_factory

    config.add_request_method(
        lambda request: get_tm_session(session_factory, request.tm),
        "db",
        reify=True,
    )
    config.add_subscriber(
        lambda _: dbengine.pool.recreate(),
        CeleryWorkerProcessInit,
    )
