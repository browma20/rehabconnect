from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from datetime import datetime
from . import Base


class SessionAuditLog(Base):
    __tablename__ = 'session_audit_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey('sessions.id'), nullable=False, index=True)
    action_type = Column(String, nullable=False)
    performed_by = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    notes = Column(String, nullable=True)

    def __repr__(self):
        return (
            f"<SessionAuditLog(id={self.id}, session_id={self.session_id}, "
            f"action_type={self.action_type}, performed_by={self.performed_by}, "
            f"timestamp={self.timestamp})>"
        )
