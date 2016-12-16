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


engine = create_engine('sqlite:///fabric_scraping.db')
Base.metadata.create_all(engine)
