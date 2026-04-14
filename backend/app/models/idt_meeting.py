from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from . import Base

class IDTMeeting(Base):
    __tablename__ = 'idt_meetings'

    idt_id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey('patients.patient_id'), nullable=False)
    meeting_datetime = Column(DateTime(timezone=True), nullable=False)
    physician_present = Column(Boolean, nullable=False)
    rn_present = Column(Boolean, nullable=False)
    pt_present = Column(Boolean, nullable=False)
    ot_present = Column(Boolean, nullable=False)
    slp_present = Column(Boolean, nullable=True)
    goals_updated = Column(Boolean, nullable=True)
    barriers = Column(String, nullable=True)
    physician_signoff = Column(DateTime(timezone=True), nullable=True)

    patient = relationship('Patient', back_populates='idt_meetings')

    def __repr__(self):
        return f"<IDTMeeting(idt_id={self.idt_id}, patient_id={self.patient_id}, meeting_datetime={self.meeting_datetime})>"
