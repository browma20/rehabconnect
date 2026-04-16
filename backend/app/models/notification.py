from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models import Base


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, index=True)  # therapist_id or family user_id
    session_id = Column(String, ForeignKey('sessions.id'), nullable=False, index=True)
    type = Column(String, nullable=False)  # e.g., SESSION_ASSIGNED, SESSION_CANCELED, SESSION_COMPLETED, SESSION_RESCHEDULED, etc.
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read = Column(Boolean, default=False, index=True)

    # Relationship to Session
    session = relationship("Session", foreign_keys=[session_id])

    def __repr__(self):
        return f"<Notification id={self.id} user_id={self.user_id} session_id={self.session_id} type={self.type} read={self.read}>"
