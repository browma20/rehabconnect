from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Therapist(Base):
    __tablename__ = "therapists"

    therapist_id = Column(String, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    discipline = Column(String, nullable=False)  # PT, OT, ST
    active = Column(Boolean, default=True)

    sessions = relationship('Session', back_populates='therapist', cascade='all, delete-orphan')