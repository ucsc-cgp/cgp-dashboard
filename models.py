#! /usr/bin/env python
import os
from datetime import datetime
from sqlalchemy import Column, DateTime,\
     Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()


class Burndown(Base):
    id = Column(Integer, primary_key=True)
    total_jobs = Column(Numeric, nullable=False, default=0)
    finished_jobs = Column(Numeric, nullable=False, default=0)
    captured_date = Column(DateTime, default=datetime.utcnow())


bd_user = os.getenv('BD_POSTGRES_USER')
bd_password = os.getenv('BD_POSTGRES_PASSWORD')
bd_table = os.getenv('BD_POSTGRES_DB')
engine = create_engine('postgresql://{}:{}@bdchart-db/{}'.format(bd_user,
                                                                 bd_password,
                                                                 bd_table))

session = sessionmaker()
session.configure(bind=engine)
Base.metadata.create_all(engine)
