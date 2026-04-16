from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session as OrmSession
from app.models.session import Session as SessionModel
from app.models.therapist import Therapist
from app.services.session_service import SessionService
from app.services.notification_service import NotificationService
from app.services.session_audit_service import SessionAuditService
from app.services.matching_service import MatchingService
from app.services.conflict_detection_service import ConflictDetectionService


class TherapistMobileService:
    def __init__(self, db: OrmSession):
        self.db = db
        self._session_service = SessionService(db)
        self._notification_service = NotificationService(db)
        self._audit_service = SessionAuditService(db)
        self._matching_service = MatchingService(db)
        self._conflict_service = ConflictDetectionService(db)

    def _get_therapist(self, therapist_id: str) -> Therapist:
        """Validate therapist exists."""
        therapist = self.db.query(Therapist).filter(
            Therapist.therapist_id == therapist_id,
            Therapist.active == True,
        ).first()
        return therapist

    def _serialize_session(self, session: SessionModel, therapist: Therapist = None) -> dict:
        """Mobile-friendly session serialization."""
        start_dt = datetime.combine(session.date, session.start_time)
        end_dt = datetime.combine(session.date, session.end_time)
        duration_minutes = int((end_dt - start_dt).total_seconds() / 60)

        return {
            "id": session.id,
            "patient_id": session.patient_id,
            "therapist_id": session.therapist_id,
            "date": session.date.isoformat(),
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat(),
            "duration_minutes": duration_minutes,
            "discipline": session.discipline,
            "notes": session.notes,
            "status": session.status,
        }

    def get_daily_schedule(self, therapist_id: str, date_value: date = None) -> dict:
        """
        Get therapist's schedule for a specific day.
        
        Returns:
            {
                "success": True/False,
                "therapist_id": "...",
                "date": "YYYY-MM-DD",
                "sessions": [...],
                "total_minutes": 0,
                "session_count": 0
            }
        """
        therapist = self._get_therapist(therapist_id)
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found or inactive",
            }

        if date_value is None:
            date_value = date.today()

        sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date == date_value,
                SessionModel.status != "canceled",
            )
            .order_by(SessionModel.start_time.asc())
            .all()
        )

        total_minutes = sum(
            int((datetime.combine(s.date, s.end_time) - datetime.combine(s.date, s.start_time)).total_seconds() / 60)
            for s in sessions
        )

        return {
            "success": True,
            "therapist_id": therapist_id,
            "therapist_name": f"{therapist.first_name} {therapist.last_name}",
            "date": date_value.isoformat(),
            "sessions": [self._serialize_session(s, therapist) for s in sessions],
            "total_minutes": total_minutes,
            "session_count": len(sessions),
        }

    def get_weekly_schedule(self, therapist_id: str, week_start: date = None) -> dict:
        """
        Get therapist's schedule for a full week.
        
        Returns:
            {
                "success": True/False,
                "therapist_id": "...",
                "week_start": "YYYY-MM-DD",
                "week_end": "YYYY-MM-DD",
                "by_day": {
                    "YYYY-MM-DD": {
                        "sessions": [...],
                        "total_minutes": 0,
                        "session_count": 0
                    }
                },
                "weekly_totals": {"total_minutes": 0, "total_sessions": 0}
            }
        """
        therapist = self._get_therapist(therapist_id)
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found or inactive",
            }

        if week_start is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())

        week_end = week_start + timedelta(days=6)

        sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date >= week_start,
                SessionModel.date <= week_end,
                SessionModel.status != "canceled",
            )
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

        by_day = {}
        total_weekly_minutes = 0
        total_weekly_sessions = 0

        for day_offset in range(7):
            current_date = week_start + timedelta(days=day_offset)
            day_key = current_date.isoformat()
            day_sessions = [s for s in sessions if s.date == current_date]
            
            day_minutes = sum(
                int((datetime.combine(s.date, s.end_time) - datetime.combine(s.date, s.start_time)).total_seconds() / 60)
                for s in day_sessions
            )

            by_day[day_key] = {
                "sessions": [self._serialize_session(s, therapist) for s in day_sessions],
                "total_minutes": day_minutes,
                "session_count": len(day_sessions),
            }

            total_weekly_minutes += day_minutes
            total_weekly_sessions += len(day_sessions)

        return {
            "success": True,
            "therapist_id": therapist_id,
            "therapist_name": f"{therapist.first_name} {therapist.last_name}",
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "by_day": by_day,
            "weekly_totals": {
                "total_minutes": total_weekly_minutes,
                "total_sessions": total_weekly_sessions,
            },
        }

    def complete_session(self, therapist_id: str, session_id: str, notes: str = None) -> dict:
        """
        Mark a session as completed (therapist action).
        
        Returns:
            {
                "success": True/False,
                "message": "...",
                "session": {...}
            }
        """
        therapist = self._get_therapist(therapist_id)
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found or inactive",
            }

        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return {
                "success": False,
                "error": "Session not found",
            }

        if session.therapist_id != therapist_id:
            return {
                "success": False,
                "error": "This session is not assigned to you",
            }

        result = self._session_service.complete_session(session_id, notes=notes)
        if result:
            return {
                "success": True,
                "message": "Session completed successfully",
                "session": result,
            }

        return {
            "success": False,
            "error": "Failed to complete session",
        }

    def cancel_session(self, therapist_id: str, session_id: str, reason: str = None) -> dict:
        """
        Cancel a session (therapist action).
        
        Returns:
            {
                "success": True/False,
                "message": "...",
                "session": {...}
            }
        """
        therapist = self._get_therapist(therapist_id)
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found or inactive",
            }

        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return {
                "success": False,
                "error": "Session not found",
            }

        if session.therapist_id != therapist_id:
            return {
                "success": False,
                "error": "This session is not assigned to you",
            }

        result = self._session_service.cancel_session(session_id, reason=reason)
        if result:
            return {
                "success": True,
                "message": "Session canceled successfully",
                "session": result,
            }

        return {
            "success": False,
            "error": "Failed to cancel session",
        }

    def reschedule_session(self, therapist_id: str, session_id: str, date_value, start_time_value, end_time_value) -> dict:
        """
        Reschedule a session (therapist action).
        
        Returns:
            {
                "success": True/False,
                "message": "...",
                "session": {...},
                "conflicts": [...]
            }
        """
        therapist = self._get_therapist(therapist_id)
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found or inactive",
            }

        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return {
                "success": False,
                "error": "Session not found",
            }

        if session.therapist_id != therapist_id:
            return {
                "success": False,
                "error": "This session is not assigned to you",
            }

        result = self._session_service.reschedule_session(
            session_id,
            date_value,
            start_time_value,
            end_time_value,
        )

        if result and result.get("success"):
            return {
                "success": True,
                "message": "Session rescheduled successfully",
                "session": result.get("session"),
            }

        if result and result.get("conflicts"):
            return {
                "success": False,
                "error": "Scheduling conflicts detected",
                "conflicts": result.get("conflicts", []),
            }

        return {
            "success": False,
            "error": result.get("reason", "Failed to reschedule session"),
        }

    def list_open_sessions(self, therapist_id: str) -> dict:
        """
        List open sessions (unassigned) matching therapist's discipline.
        
        Returns:
            {
                "success": True/False,
                "therapist_id": "...",
                "discipline": "PT",
                "open_sessions": [...],
                "session_count": 0
            }
        """
        therapist = self._get_therapist(therapist_id)
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found or inactive",
            }

        open_sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == None,  # noqa: E711
                SessionModel.discipline == therapist.discipline,
                SessionModel.status != "canceled",
                SessionModel.status != "completed",
                SessionModel.date >= date.today(),
            )
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

        return {
            "success": True,
            "therapist_id": therapist_id,
            "discipline": therapist.discipline,
            "open_sessions": [self._serialize_session(s, therapist) for s in open_sessions],
            "session_count": len(open_sessions),
        }

    def pickup_session(self, therapist_id: str, session_id: str) -> dict:
        """
        Therapist picks up an open session (shift pickup).
        
        Returns:
            {
                "success": True/False,
                "message": "...",
                "session": {...},
                "conflicts": [...]
            }
        """
        therapist = self._get_therapist(therapist_id)
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found or inactive",
            }

        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return {
                "success": False,
                "error": "Session not found",
            }

        if session.therapist_id is not None:
            return {
                "success": False,
                "error": "This session is already assigned to someone else",
            }

        if session.discipline != therapist.discipline:
            return {
                "success": False,
                "error": f"You specialize in {therapist.discipline}, but this session requires {session.discipline}",
            }

        result = self._session_service.request_shift_pickup(session_id, therapist_id)

        if result and result.get("success"):
            return {
                "success": True,
                "message": "Session picked up successfully",
                "session": result.get("session"),
            }

        if result and result.get("conflicts"):
            return {
                "success": False,
                "error": "You have scheduling conflicts with this session",
                "conflicts": result.get("conflicts", []),
            }

        return {
            "success": False,
            "error": result.get("error", "Failed to pick up session"),
        }

    def get_notifications(self, therapist_id: str, unread_only: bool = False) -> dict:
        """
        Get therapist's notifications.
        
        Returns:
            {
                "success": True/False,
                "therapist_id": "...",
                "notifications": [...],
                "unread_count": 0,
                "total_count": 0
            }
        """
        therapist = self._get_therapist(therapist_id)
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found or inactive",
            }

        notifications = self._notification_service.get_notifications(therapist_id, unread_only=unread_only)
        unread_count = self._notification_service.get_unread_count(therapist_id)

        return {
            "success": True,
            "therapist_id": therapist_id,
            "notifications": notifications,
            "unread_count": unread_count,
            "total_count": len(notifications),
        }
