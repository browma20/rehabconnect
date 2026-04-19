from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text

from app.database import Base


class OverrideLog(Base):
    __tablename__ = "override_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    recommended_therapist_id = Column(String, nullable=True, index=True)
    chosen_therapist_id = Column(String, nullable=False, index=True)
    recommended_score = Column(Float, nullable=True)
    chosen_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    risk_summary = Column(JSON, nullable=True)
    data_gaps = Column(JSON, nullable=True)
    override_reason = Column(Text, nullable=False)
    overridden_by = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return (
            f"<OverrideLog(id={self.id}, session_id={self.session_id}, "
            f"recommended_therapist_id={self.recommended_therapist_id}, "
            f"chosen_therapist_id={self.chosen_therapist_id}, timestamp={self.timestamp})>"
        )
