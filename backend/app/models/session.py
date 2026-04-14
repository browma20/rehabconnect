from sqlalchemy import Column, String, Date, Time, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from . import Base
import uuid

class Session(Base):
    __tablename__ = 'sessions'

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    therapist_id = Column(String, ForeignKey('therapists.therapist_id'), nullable=True)
    patient_id = Column(String, ForeignKey('patients.patient_id'), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    discipline = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String, nullable=False, default='scheduled')
    completed_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String, nullable=True)

    therapist = relationship('Therapist', back_populates='sessions')
    patient = relationship('Patient', back_populates='sessions')

    def __repr__(self):
        return f"<Session(id={self.id}, therapist_id={self.therapist_id}, patient_id={self.patient_id}, discipline={self.discipline})>"