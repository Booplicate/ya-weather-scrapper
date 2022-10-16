"""
Module imlements an sql connector
"""


import datetime
import sqlalchemy
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    select,
    insert,
    update,
    delete,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)


ENGINE_URL = "sqlite:///yaws.db"

engine = None
Base = declarative_base()
metadata = Base.metadata
SessionFactory = None


class ScrapResult(Base):
    """
    Represents a result of weather scrapping
    """
    __tablename__ = "scrap_result"

    id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False)
    dt = Column(DateTime, nullable=False)
    result = Column(Boolean, nullable=False)

    def __str__(self):
        return f"ScrapResult(city='{self.city}', dt={self.dt}, result={self.result})"

    __repr__ = __str__


def init(engine_url: str|None = None):
    global engine, SessionFactory

    if engine_url is None:
        engine_url = ENGINE_URL

    engine = sqlalchemy.create_engine(engine_url)
    SessionFactory = sessionmaker(engine)

    metadata.create_all(engine)

def connect():
    if engine is None:
        raise RuntimeError("Trying to access sql db prior to init")

    return SessionFactory()

def add_new_result_entry(
    city: str,
    result: bool,
    dt: datetime.datetime|None = None
):
    """
    Adds a new result entry to the local datebase
    """
    with connect() as sesh:
        if dt is None:
            dt = datetime.datetime.utcnow()
        entry = ScrapResult(city=city, dt=dt, result=result)
        sesh.add(entry)
        sesh.commit()
