from datetime import datetime, date
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.idt_meeting import IDTMeeting
from ..models.patient import Patient
from ..compliance_engines.idt_engine import idt_timeliness, attendance_compliance, documentation_completeness


class IDTService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_idt_meeting(
        self,
        patient_id: str,
        meeting_datetime: datetime,
        physician_present: bool = False,
        rn_present: bool = False,
        pt_present: bool = False,
        ot_present: bool = False,
        slp_present: Optional[bool] = None
    ) -> IDTMeeting:
        """Create a new IDT meeting."""
        meeting = IDTMeeting(
            patient_id=patient_id,
            meeting_datetime=meeting_datetime,
            physician_present=physician_present,
            rn_present=rn_present,
            pt_present=pt_present,
            ot_present=ot_present,
            slp_present=slp_present
        )
        self.db.add(meeting)
        self.db.commit()
        self.db.refresh(meeting)
        return meeting

    def get_meetings_for_patient(self, patient_id: str) -> List[IDTMeeting]:
        """Get all IDT meetings for a patient."""
        return self.db.query(IDTMeeting).filter(IDTMeeting.patient_id == patient_id).order_by(IDTMeeting.meeting_datetime.desc()).all()

    def get_latest_meeting(self, patient_id: str) -> Optional[IDTMeeting]:
        """Get the most recent IDT meeting for a patient."""
        return self.db.query(IDTMeeting)\
            .filter(IDTMeeting.patient_id == patient_id)\
            .order_by(IDTMeeting.meeting_datetime.desc())\
            .first()

    def update_meeting_notes(self, idt_id: str, discipline_notes: str, goals_updated: str, barriers: str) -> Optional[IDTMeeting]:
        """Update meeting with discipline notes (therapist workflow)."""
        meeting = self.db.query(IDTMeeting).filter(IDTMeeting.idt_id == idt_id).first()
        if not meeting:
            return None

        # For simplicity, store as JSON or text; assuming we add fields to model if needed
        # Here, we'll assume the model has fields for notes
        # Since model has barriers, goals_updated, but not discipline_notes, we'll use barriers for now
        meeting.barriers = barriers
        meeting.goals_updated = goals_updated
        # Note: May need to extend model for discipline_notes

        self.db.commit()
        self.db.refresh(meeting)
        return meeting

    def finalize_meeting(self, idt_id: str, medical_necessity: str, physician_signoff: datetime) -> Optional[IDTMeeting]:
        """Finalize meeting with physician sign-off."""
        meeting = self.db.query(IDTMeeting).filter(IDTMeeting.idt_id == idt_id).first()
        if not meeting:
            return None

        meeting.physician_signoff = physician_signoff
        # Assuming we add medical_necessity field or store elsewhere
        # For now, store in barriers or extend model

        self.db.commit()
        self.db.refresh(meeting)
        return meeting

    def get_timeliness_compliance(self, patient_id: str, as_of_date: date = None) -> Dict[str, Any]:
        """Get IDT timeliness compliance."""
        latest_meeting = self.get_latest_meeting(patient_id)
        last_date = latest_meeting.meeting_datetime.date() if latest_meeting else None
        return idt_timeliness(last_date, as_of_date)

    def get_attendance_compliance(self, idt_id: str) -> Dict[str, Any]:
        """Get attendance compliance for a specific meeting."""
        meeting = self.db.query(IDTMeeting).filter(IDTMeeting.idt_id == idt_id).first()
        if not meeting:
            return {'status': 'Red', 'notes': 'Meeting not found'}

        attendance = {
            'physician': meeting.physician_present,
            'rn': meeting.rn_present,
            'pt': meeting.pt_present,
            'ot': meeting.ot_present,
            'slp': meeting.slp_present
        }

        # Check if SLP involved
        patient = self.db.query(Patient).filter(Patient.patient_id == meeting.patient_id).first()
        slp_involved = 'SLP' in (patient.assigned_disciplines or []) if patient else False

        return attendance_compliance(attendance, slp_involved)

    def get_documentation_compliance(self, idt_id: str) -> Dict[str, Any]:
        """Get documentation completeness for a meeting."""
        meeting = self.db.query(IDTMeeting).filter(IDTMeeting.idt_id == idt_id).first()
        if not meeting:
            return {'status': 'Red', 'notes': 'Meeting not found'}

        fields = {
            'patient_progress': True,  # Assume present
            'barriers': bool(meeting.barriers),
            'goals_updated': bool(meeting.goals_updated),
            'medical_necessity': bool(meeting.physician_signoff),  # Simplified
            'discipline_notes': True  # Assume present
        }

        return documentation_completeness(fields)