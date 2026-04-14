from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base

class User(Base):
    __tablename__ = 'users'

    user_id = Column(String, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)

    audit_logs = relationship('AuditLog', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User(user_id={self.user_id}, name={self.first_name} {self.last_name}, role={self.role})>"
