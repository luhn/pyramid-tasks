from sqlalchemy import Column, Integer

from .meta import Base


class Ledger(Base):
    __tablename__ = "ledger"
    id = Column(Integer, primary_key=True)
    amount = Column(Integer)
