import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Time, DateTime, ForeignKey
from . import Base


class TherapistAvailability(Base):
    __tablename__ = "therapist_availability"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    therapist_id = Column(String, ForeignKey("therapists.therapist_id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Mon ... 6=Sun
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    max_sessions = Column(Integer, nullable=True)
    max_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TherapistTimeOff(Base):
    __tablename__ = "therapist_time_off"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    therapist_id = Column(String, ForeignKey("therapists.therapist_id"), nullable=False, index=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    reason = Column(String, nullable=True)
