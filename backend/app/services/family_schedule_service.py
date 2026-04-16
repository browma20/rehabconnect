from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session as OrmSession
from app.models.session import Session as SessionModel
from app.models.therapist import Therapist
from app.models.notification import Notification
from app.models.patient import Patient


class FamilyScheduleService:
    def __init__(self, db: OrmSession):
        self.db = db

    def _get_patient(self, patient_id: str) -> Patient:
        """Validate patient exists."""
        patient = self.db.query(Patient).filter(Patient.patient_id == patient_id).first()
        return patient

    def _get_therapist_name(self, therapist_id: str) -> str:
        """Get therapist name, or 'Unassigned' if none."""
        if not therapist_id:
            return "Unassigned"
        
        therapist = self.db.query(Therapist).filter(Therapist.therapist_id == therapist_id).first()
        if therapist:
            return f"{therapist.first_name} {therapist.last_name}"
        return "Unknown"

    def _session_has_updates(self, session_id: str) -> bool:
        """Check if session has unread notifications."""
        unread_notification = (
            self.db.query(Notification)
            .filter(
                Notification.session_id == session_id,
                Notification.read == False,
            )
            .first()
        )
        return unread_notification is not None

    def _get_latest_notification_message(self, session_id: str) -> str:
        """Get the most recent notification message for a session."""
        notification = (
            self.db.query(Notification)
            .filter(Notification.session_id == session_id)
            .order_by(Notification.created_at.desc())
            .first()
        )
        return notification.message if notification else None

    def _serialize_session(self, session: SessionModel) -> dict:
        """Serialize a session for family view."""
        start_dt = datetime.combine(session.date, session.start_time)
        end_dt = datetime.combine(session.date, session.end_time)
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

        has_updates = self._session_has_updates(session.id)
        latest_update = self._get_latest_notification_message(session.id) if has_updates else None

        return {
            "id": session.id,
            "discipline": session.discipline,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat(),
            "duration_minutes": duration_minutes,
            "therapist_name": self._get_therapist_name(session.therapist_id),
            "status": session.status,
            "notes": session.notes,
            "has_updates": has_updates,
            "latest_update": latest_update,
        }

    def get_weekly_summary(self, patient_id: str, week_start: date = None) -> dict:
        """
        Get complete weekly summary for a patient.
        
        Args:
            patient_id: Patient identifier
            week_start: Start of week (default: Monday of current week)
        
        Returns:
            {
                "success": True/False,
                "patient_id": "...",
                "patient_name": "...",
                "week_start": "YYYY-MM-DD",
                "week_end": "YYYY-MM-DD",
                "days": {
                    "YYYY-MM-DD": [
                        {
                            "id": "...",
                            "discipline": "PT",
                            "start_time": "HH:MM:SS",
                            "end_time": "HH:MM:SS",
                            "duration_minutes": 60,
                            "therapist_name": "John Doe",
                            "status": "scheduled",
                            "notes": "...",
                            "has_updates": False,
                            "latest_update": "..."
                        }
                    ]
                },
                "summary": {
                    "total_sessions": 5,
                    "completed": 2,
                    "canceled": 0,
                    "upcoming": 3,
                    "total_minutes": 300
                }
            }
        """
        patient = self._get_patient(patient_id)
        if not patient:
            return {
                "success": False,
                "error": "Patient not found",
            }

        if week_start is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.patient_id == patient_id,
                SessionModel.date >= week_start,
                SessionModel.date <= week_end,
            )
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

        # Group sessions by date
        days = {}
        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            day_key = current_date.isoformat()
            day_sessions = [s for s in sessions if s.date == current_date]
            days[day_key] = [self._serialize_session(s) for s in day_sessions]

        # Calculate summary totals
        total_sessions = len(sessions)
        completed = sum(1 for s in sessions if s.status == "completed")
        canceled = sum(1 for s in sessions if s.status == "canceled")
        upcoming = sum(1 for s in sessions if s.status in ("scheduled", "unassigned"))
        total_minutes = sum(
            int((datetime.combine(s.date, s.end_time) - datetime.combine(s.date, s.start_time)).total_seconds() / 60)
            for s in sessions
        )

        return {
            "success": True,
            "patient_id": patient_id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "days": days,
            "summary": {
                "total_sessions": total_sessions,
                "completed": completed,
                "canceled": canceled,
                "upcoming": upcoming,
                "total_minutes": total_minutes,
            },
        }

    def get_patients_for_family(self, family_id: str) -> list:
        """
        Get all patients associated with a family.
        Note: This is a placeholder assuming a family_id field or relationship exists on Patient.
        In production, this would use a family_members or similar junction table.
        """
        # TODO: Implement family member lookup once family model is finalized
        # For now, this returns empty list - to be implemented based on actual schema
        return []

    def get_family_weekly_summary(self, family_id: str, week_start: date = None) -> dict:
        """
        Get weekly summary for all patients in a family.
        
        Returns:
            {
                "success": True/False,
                "family_id": "...",
                "week_start": "YYYY-MM-DD",
                "week_end": "YYYY-MM-DD",
                "patients": [
                    {
                        "patient_id": "...",
                        "patient_name": "...",
                        "days": {...},
                        "summary": {...}
                    }
                ]
            }
        """
        patients = self.get_patients_for_family(family_id)
        
        if not patients:
            return {
                "success": False,
                "error": "No patients found for this family or family not found",
            }

        if week_start is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        patient_summaries = []
        for patient_id in patients:
            summary = self.get_weekly_summary(patient_id, week_start)
            if summary.get("success"):
                patient_summaries.append(summary)

        return {
            "success": True,
            "family_id": family_id,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "patients": patient_summaries,
        }
