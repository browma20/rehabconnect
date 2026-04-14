from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base

class MedicalNecessityRecord(Base):
    __tablename__ = 'medical_necessity_records'

    record_id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey('patients.patient_id'), nullable=False)
    statement = Column(String, nullable=False)
    barriers = Column(String, nullable=True)
    clinical_reasoning = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    discipline = Column(String, nullable=False)

    patient = relationship('Patient', back_populates='medical_necessity_records')

    def __repr__(self):
        return f"<MedicalNecessityRecord(record_id={self.record_id}, patient_id={self.patient_id})>"
