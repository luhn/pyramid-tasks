import zope.sqlalchemy
from sqlalchemy import Column, Integer, engine_from_config, func
from sqlalchemy.orm import declarative_base, sessionmaker


def includeme(config):
    config.add_settings(
        {
            "tm.manager_hook": "pyramid_tm.explicit_manager",
        }
    )
    config.include("pyramid_tm")
    config.include("pyramid_tasks.transaction")

    config.add_settings({"sqlalchemy.url": "sqlite:///db.sqlite3"})
    dbengine = get_engine(config.get_settings())
    Base.metadata.drop_all(bind=dbengine)
    Base.metadata.create_all(bind=dbengine)

    session_factory = get_session_factory(dbengine)
    config.registry["dbsession_factory"] = session_factory

    config.add_request_method(
        lambda request: get_tm_session(session_factory, request.tm),
        "db",
        reify=True,
    )

    config.register_task(increment_task, name="increment")
    config.register_task(total_task, name="total")


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


Base = declarative_base()


class Ledger(Base):
    __tablename__ = "ledger"
    id = Column(Integer, primary_key=True)
    amount = Column(Integer)


def increment_task(request, value=1):
    request.db.add(Ledger(amount=value))


def total_task(request):
    return request.db.query(func.sum(Ledger.amount)).scalar() or 0
