from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base

class TherapySession(Base):
    __tablename__ = 'therapy_sessions'

    session_id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey('patients.patient_id'), nullable=False)
    discipline = Column(String, nullable=False)
    delivered_minutes = Column(Integer, nullable=False)
    scheduled_minutes = Column(Integer, nullable=True)
    missed_minutes = Column(Integer, nullable=True)
    reason_code = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    source = Column(String, nullable=False)
    therapist_id = Column(String, nullable=True)

    patient = relationship('Patient', back_populates='therapy_sessions')

    @property
    def duration_minutes(self) -> int:
        """Alias for delivered_minutes (API compatibility)."""
        return self.delivered_minutes

    def __repr__(self):
        return f"<TherapySession(session_id={self.session_id}, patient_id={self.patient_id}, discipline={self.discipline})>"
