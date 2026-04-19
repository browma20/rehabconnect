
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Text

from app.database import Base


class AutomationAuditEntry(Base):
    __tablename__ = "automation_audit_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)
    recommended_option = Column(JSON, nullable=True)
    recommended_score = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    confidence_components = Column(JSON, nullable=True)
    risks = Column(JSON, nullable=True)
    data_gaps = Column(JSON, nullable=True)
    human_choice = Column(JSON, nullable=True)
    override_reason = Column(Text, nullable=True)
    performed_by = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return (
            f"<AutomationAuditEntry(id={self.id}, session_id={self.session_id}, "
            f"event_type={self.event_type}, timestamp={self.timestamp})>"
        )
