from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class PhysicianEvaluation(Base):
    __tablename__ = 'physician_evaluations'

    evaluation_id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey('patients.patient_id'), nullable=False)
    physician_id = Column(String, nullable=False)
    physician_name = Column(String, nullable=False)
    evaluation_datetime = Column(DateTime(timezone=True), nullable=False)
    first_day_compliance = Column(Boolean, nullable=True)
    notes = Column(String, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    patient = relationship('Patient', back_populates='physician_evaluations')
    audit_logs = relationship('AuditLog', back_populates='physician_evaluation', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<PhysicianEvaluation(evaluation_id={self.evaluation_id}, patient_id={self.patient_id}, physician_id={self.physician_id})>"
