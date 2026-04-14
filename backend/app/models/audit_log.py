from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    audit_id = Column(String, primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    user_role = Column(String, nullable=False)
    patient_id = Column(String, ForeignKey('patients.patient_id'), nullable=True)
    action_type = Column(String, nullable=False)
    previous_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    source = Column(String, nullable=False)

    user = relationship('User', back_populates='audit_logs')
    patient = relationship('Patient', back_populates='audit_logs')
    physician_evaluation_id = Column(String, ForeignKey('physician_evaluations.evaluation_id'), nullable=True)
    physician_evaluation = relationship('PhysicianEvaluation', back_populates='audit_logs')

    def __repr__(self):
        return f"<AuditLog(audit_id={self.audit_id}, user_id={self.user_id}, action_type={self.action_type})>"
