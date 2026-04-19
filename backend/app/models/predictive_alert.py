from datetime import datetime
from sqlalchemy import Boolean, Column, Date, DateTime, Integer, JSON, String

from app.database import Base


class PredictiveAlert(Base):
    __tablename__ = "predictive_alerts"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False, index=True)
    severity = Column(String, nullable=False, index=True)
    message = Column(String, nullable=False)
    effective_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved = Column(Boolean, default=False, index=True)
    metadata_json = Column("metadata", JSON, nullable=True)

    def __repr__(self):
        return (
            f"<PredictiveAlert id={self.id} type={self.type} severity={self.severity} "
            f"effective_date={self.effective_date} resolved={self.resolved}>"
        )
