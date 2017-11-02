#! /usr/bin/env python
import os
from datetime import datetime
from sqlalchemy import Column, DateTime,\
     Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from time import sleep

Base = declarative_base()


class Burndown(Base):
    __tablename__ = 'burndown'
    id = Column(Integer, primary_key=True)
    total_jobs = Column(Numeric, nullable=False, default=0)
    finished_jobs = Column(Numeric, nullable=False, default=0)
    captured_date = Column(DateTime, default=datetime.utcnow())


def initialize_table():
    bd_user = os.getenv('BD_POSTGRES_USER')
    bd_password = os.getenv('BD_POSTGRES_PASSWORD')
    bd_table = os.getenv('BD_POSTGRES_DB')
    db_url = 'postgresql://{}:{}@bdchart-db/{}'.format(bd_user, bd_password,
                                                       bd_table)
    engine = create_engine(db_url)
    session = sessionmaker()
    session.configure(bind=engine)
    Base.metadata.create_all(engine)
    # We have sleep here because it appears that the call to create call is non-blocking
    # so we need to wait a little bit for the subprocess to create the table.
    sleep(5)
    session.close_all()
    engine.dispose()


def get_all():
    bd_user = os.getenv('BD_POSTGRES_USER')
    bd_password = os.getenv('BD_POSTGRES_PASSWORD')
    bd_table = os.getenv('BD_POSTGRES_DB')
    db_url = 'postgresql://{}:{}@bdchart-db/{}'.format(bd_user, bd_password,
                                                       bd_table)
    engine = create_engine(db_url)
    session = sessionmaker()
    session.configure(bind=engine)
    s = session()
    query_object = s.query(Burndown).order_by(Burndown.captured_date.asc()).all()
    query_list = [x for x in query_object]
    session.close_all()
    engine.dispose()
    return query_list
