from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import os

Base = declarative_base()


class TopCrashes(Base):
    __tablename__ = 'top_crashes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(20))
    app_version = Column(String(16))
    crash_name = Column(String(40))
    crash_subtitle = Column(String(80))
    first_seen = Column(String(16))
    last_seen = Column(String(16))
    number_of_notes = Column(Integer)
    percent_rooted = Column(String(40))
    os_version = Column(Integer)
    device = Column(String(16))
    number_of_crashes = Column(Integer)
    number_of_users = Column(Integer)
    crash_rate = Column(String(16))
    run_time = Column(Integer)
    ownership = Column(String(16))


engine = create_engine('sqlite:///{}'.format(os.environ['DB_LOCATION']))
Base.metadata.create_all(engine)
