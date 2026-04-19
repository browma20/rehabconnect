from sqlalchemy import Column, String, Date, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Patient(Base):
    __tablename__ = 'patients'

    patient_id = Column(String, primary_key=True)
    mrn = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    admission_datetime = Column(DateTime(timezone=True), nullable=False)
    discharge_datetime = Column(DateTime(timezone=True), nullable=True)
    primary_diagnosis = Column(String, nullable=True)
    comorbidities = Column(JSON, nullable=True)
    assigned_disciplines = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    physician_evaluations = relationship('PhysicianEvaluation', back_populates='patient', cascade='all, delete-orphan')
    sessions = relationship('Session', back_populates='patient', cascade='all, delete-orphan')
    therapy_sessions = relationship('TherapySession', back_populates='patient', cascade='all, delete-orphan')
    functional_scores = relationship('FunctionalScore', back_populates='patient', cascade='all, delete-orphan')
    idt_meetings = relationship('IDTMeeting', back_populates='patient', cascade='all, delete-orphan')
    medical_necessity_records = relationship('MedicalNecessityRecord', back_populates='patient', cascade='all, delete-orphan')
    risk_scores = relationship('RiskScore', back_populates='patient', cascade='all, delete-orphan')
    audit_logs = relationship('AuditLog', back_populates='patient', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Patient(patient_id={self.patient_id}, name={self.first_name} {self.last_name})>"
