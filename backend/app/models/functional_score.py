from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class FunctionalScore(Base):
    __tablename__ = 'functional_scores'

    score_id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey('patients.patient_id'), nullable=False)
    discipline = Column(String, nullable=False)
    score_type = Column(String, nullable=False)
    score_value = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    notes = Column(String, nullable=True)
    source = Column(String, nullable=False)

    patient = relationship('Patient', back_populates='functional_scores')

    def __repr__(self):
        return f"<FunctionalScore(score_id={self.score_id}, patient_id={self.patient_id}, score_type={self.score_type})>"
