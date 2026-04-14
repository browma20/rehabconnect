from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class RiskScore(Base):
    __tablename__ = 'risk_scores'

    risk_id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey('patients.patient_id'), nullable=False)
    score = Column(Integer, nullable=False)
    risk_category = Column(String, nullable=False)
    top_drivers = Column(JSON, nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    patient = relationship('Patient', back_populates='risk_scores')

    def __repr__(self):
        return f"<RiskScore(risk_id={self.risk_id}, patient_id={self.patient_id}, score={self.score}, category={self.risk_category})>"
