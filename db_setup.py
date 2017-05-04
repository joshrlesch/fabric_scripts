from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()



class ReleaseSummary(Base):
    __tablename__ = 'release_summary'

    id = Column(Integer, primary_key=True, autoincrement=True)
    app = Column(String(20))
    branch = Column(String(60))
    sessions = Column(Integer)
    total_time = Column(Integer)
    crash_free_devices = Column(String(10))
    crash_free_sessions = Column(String(10))
    devices = Column(Integer)
    crashed = Column(Integer)
    sessions_crashed = Column(Integer)
    pr_number = Column(Integer)
    pr_created_at = Column(DateTime)
    pr_updated_at = Column(DateTime)
    pr_closed_at = Column(DateTime)
    pr_merged_at = Column(DateTime)


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


engine = create_engine('sqlite:///fabric_scraping.db')
Base.metadata.create_all(engine)
