from datetime import date, time, timedelta, datetime
from sqlalchemy.orm import Session as OrmSession
from backend.app.models.session import Session as SessionModel
from backend.app.models.therapist import Therapist
from backend.app.services.conflict_detection_service import ConflictDetectionService
from backend.app.services.session_audit_service import SessionAuditService
from backend.app.services.notification_service import NotificationService


class SessionService:
    def __init__(self, db: OrmSession):
        self.db = db

    def _parse_date(self, value):
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        raise ValueError('Invalid date format; expected YYYY-MM-DD')

    def _parse_time(self, value):
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            return time.fromisoformat(value)
        raise ValueError('Invalid time format; expected HH:MM[:SS]')

    def _duration_minutes(self, session):
        start_dt = datetime.combine(session.date, session.start_time)
        end_dt = datetime.combine(session.date, session.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)

    def _serialize_session(self, session):
        return {
            "id": session.id,
            "therapist_id": session.therapist_id,
            "patient_id": session.patient_id,
            "date": session.date.isoformat(),
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat(),
            "duration_minutes": self._duration_minutes(session),
            "discipline": session.discipline,
            "notes": session.notes,
            "status": session.status,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "canceled_at": session.canceled_at.isoformat() if session.canceled_at else None,
            "cancellation_reason": session.cancellation_reason,
        }

    def create_session(self, data):
        therapist_id = data.get("therapist_id")
        status = data.get("status")
        if not status:
            status = "scheduled" if therapist_id else "unassigned"

        session = SessionModel(
            id=data.get("id"),
            therapist_id=therapist_id,
            patient_id=data["patient_id"],
            date=self._parse_date(data["date"]),
            start_time=self._parse_time(data["start_time"]),
            end_time=self._parse_time(data["end_time"]),
            discipline=data["discipline"],
            notes=data.get("notes"),
            status=status,
)
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_session_by_id(self, session_id: str):
        return self.db.query(SessionModel).filter(SessionModel.id == session_id).first()

    def list_sessions(self):
        return self.db.query(SessionModel).all()

    def get_sessions_by_therapist(self, therapist_id: str):
        return self.db.query(SessionModel).filter(SessionModel.therapist_id == therapist_id).all()

    def get_sessions_by_patient(self, patient_id: str):
        return self.db.query(SessionModel).filter(SessionModel.patient_id == patient_id).all()

    def get_schedule_for_patient(self, patient_id: str, days: int = 14):
        today = date.today()
        end_date = today + timedelta(days=days)

        results = (
            self.db.query(SessionModel, Therapist)
            .join(Therapist, SessionModel.therapist_id == Therapist.therapist_id)
            .filter(SessionModel.patient_id == patient_id)
            .filter(SessionModel.date >= today)
            .filter(SessionModel.date <= end_date)
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

        return [
            {
                "id": session.id,
                "therapist_id": session.therapist_id,
                "patient_id": session.patient_id,
                "date": session.date.isoformat(),
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat(),
                "duration_minutes": self._duration_minutes(session),
                "discipline": session.discipline,
                "notes": session.notes,
                "therapist_first_name": therapist.first_name,
                "therapist_last_name": therapist.last_name,
            }
            for session, therapist in results
        ]

    def get_grouped_schedule_for_patient(self, patient_id: str, days: int = 14):
        today = date.today()
        end_date = today + timedelta(days=days)

        results = (
            self.db.query(SessionModel, Therapist)
            .join(Therapist, SessionModel.therapist_id == Therapist.therapist_id)
            .filter(SessionModel.patient_id == patient_id)
            .filter(SessionModel.date >= today)
            .filter(SessionModel.date <= end_date)
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

        grouped_schedule = {}
        for session, therapist in results:
            date_key = session.date.isoformat()
            if date_key not in grouped_schedule:
                grouped_schedule[date_key] = []

            grouped_schedule[date_key].append(
                {
                    "id": session.id,
                    "therapist_id": session.therapist_id,
                    "patient_id": session.patient_id,
                    "date": session.date.isoformat(),
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat(),
                    "duration_minutes": self._duration_minutes(session),
                    "discipline": session.discipline,
                    "notes": session.notes,
                    "therapist_first_name": therapist.first_name,
                    "therapist_last_name": therapist.last_name,
                }
            )

        return grouped_schedule
    
    def get_next_session_for_patient(self, patient_id: str):
        today = date.today()

        result = (
            self.db.query(SessionModel, Therapist)
            .join(Therapist, SessionModel.therapist_id == Therapist.therapist_id)
            .filter(SessionModel.patient_id == patient_id)
            .filter(SessionModel.date >= today)
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .first()
        )

        if not result:
            return None

        session, therapist = result

        return {
            "id": session.id,
            "therapist_id": session.therapist_id,
            "patient_id": session.patient_id,
            "date": session.date.isoformat(),
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat(),
            "duration_minutes": self._duration_minutes(session),
            "discipline": session.discipline,
            "notes": session.notes,
            "therapist_first_name": therapist.first_name,
            "therapist_last_name": therapist.last_name,
        }

    def get_todays_schedule_for_patient(self, patient_id: str):
        today = date.today()

        results = (
            self.db.query(SessionModel, Therapist)
            .join(Therapist, SessionModel.therapist_id == Therapist.therapist_id)
            .filter(SessionModel.patient_id == patient_id)
            .filter(SessionModel.date == today)
            .order_by(SessionModel.start_time.asc())
            .all()
        )

        return [
            {
                "id": session.id,
                "therapist_id": session.therapist_id,
                "patient_id": session.patient_id,
                "date": session.date.isoformat(),
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat(),
                "duration_minutes": self._duration_minutes(session),
                "discipline": session.discipline,
                "notes": session.notes,
                "therapist_first_name": therapist.first_name,
                "therapist_last_name": therapist.last_name,
            }
            for session, therapist in results
        ]

    def get_todays_schedule_for_therapist(self, therapist_id: str):
        today = date.today()

        results = (
            self.db.query(SessionModel, Therapist)
            .join(Therapist, SessionModel.therapist_id == Therapist.therapist_id)
            .filter(SessionModel.therapist_id == therapist_id)
            .filter(SessionModel.date == today)
            .order_by(SessionModel.start_time.asc())
            .all()
        )

        return [
            {
                "id": session.id,
                "therapist_id": session.therapist_id,
                "patient_id": session.patient_id,
                "date": session.date.isoformat(),
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat(),
                "duration_minutes": self._duration_minutes(session),
                "discipline": session.discipline,
                "notes": session.notes,
                "therapist_first_name": therapist.first_name,
                "therapist_last_name": therapist.last_name,
            }
            for session, therapist in results
        ]

    def get_grouped_schedule_for_therapist(self, therapist_id: str, days: int = 7):
        today = date.today()
        end_date = today + timedelta(days=days)

        results = (
            self.db.query(SessionModel, Therapist)
            .join(Therapist, SessionModel.therapist_id == Therapist.therapist_id)
            .filter(SessionModel.therapist_id == therapist_id)
            .filter(SessionModel.date >= today)
            .filter(SessionModel.date <= end_date)
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

        grouped_schedule = {}
        for session, therapist in results:
            date_key = session.date.isoformat()
            if date_key not in grouped_schedule:
                grouped_schedule[date_key] = []

            grouped_schedule[date_key].append(
                {
                    "id": session.id,
                    "therapist_id": session.therapist_id,
                    "patient_id": session.patient_id,
                    "date": session.date.isoformat(),
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat(),
                    "duration_minutes": self._duration_minutes(session),
                    "discipline": session.discipline,
                    "notes": session.notes,
                    "therapist_first_name": therapist.first_name,
                    "therapist_last_name": therapist.last_name,
                }
            )

        return grouped_schedule

    def get_weekly_schedule_for_therapist(self, therapist_id: str, days: int = 7):
        today = date.today()
        end_date = today + timedelta(days=days)

        results = (
            self.db.query(SessionModel, Therapist)
            .join(Therapist, SessionModel.therapist_id == Therapist.therapist_id)
            .filter(SessionModel.therapist_id == therapist_id)
            .filter(SessionModel.date >= today)
            .filter(SessionModel.date <= end_date)
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

        grouped_schedule = {}
        for session, therapist in results:
            date_key = session.date.isoformat()
            if date_key not in grouped_schedule:
                grouped_schedule[date_key] = []

            grouped_schedule[date_key].append(
                {
                    "id": session.id,
                    "therapist_id": session.therapist_id,
                    "patient_id": session.patient_id,
                    "date": session.date.isoformat(),
                    "start_time": session.start_time.isoformat(),
                    "end_time": session.end_time.isoformat(),
                    "duration_minutes": self._duration_minutes(session),
                    "discipline": session.discipline,
                    "notes": session.notes,
                    "therapist_first_name": therapist.first_name,
                    "therapist_last_name": therapist.last_name,
                }
            )

        return grouped_schedule

    def get_next_session_for_therapist(self, therapist_id: str):
        today = date.today()

        result = (
            self.db.query(SessionModel, Therapist)
            .join(Therapist, SessionModel.therapist_id == Therapist.therapist_id)
            .filter(SessionModel.therapist_id == therapist_id)
            .filter(SessionModel.date >= today)
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .first()
        )

        if not result:
            return None

        session, therapist = result

        return {
            "id": session.id,
            "therapist_id": session.therapist_id,
            "patient_id": session.patient_id,
            "date": session.date.isoformat(),
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat(),
            "duration_minutes": self._duration_minutes(session),
            "discipline": session.discipline,
            "notes": session.notes,
            "therapist_first_name": therapist.first_name,
            "therapist_last_name": therapist.last_name,
        }

    def get_weekly_summary_for_therapist(self, therapist_id: str, days: int = 7):
        today = date.today()
        end_date = today + timedelta(days=days)

        results = (
            self.db.query(SessionModel, Therapist)
            .join(Therapist, SessionModel.therapist_id == Therapist.therapist_id)
            .filter(SessionModel.therapist_id == therapist_id)
            .filter(SessionModel.date >= today)
            .filter(SessionModel.date <= end_date)
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

        total_sessions = 0
        total_minutes = 0
        unique_patients = set()
        first_session = None
        last_session = None
        by_day = {}
        by_discipline = {}

        for session, therapist in results:
            mins = self._duration_minutes(session)
            total_sessions += 1
            total_minutes += mins
            unique_patients.add(session.patient_id)

            start_dt = datetime.combine(session.date, session.start_time)
            end_dt = datetime.combine(session.date, session.end_time)

            if first_session is None or start_dt < first_session:
                first_session = start_dt
            if last_session is None or end_dt > last_session:
                last_session = end_dt

            date_key = session.date.isoformat()
            if date_key not in by_day:
                by_day[date_key] = {"sessions": 0, "minutes": 0}
            by_day[date_key]["sessions"] += 1
            by_day[date_key]["minutes"] += mins

            disc = session.discipline
            if disc not in by_discipline:
                by_discipline[disc] = {"sessions": 0, "minutes": 0}
            by_discipline[disc]["sessions"] += 1
            by_discipline[disc]["minutes"] += mins

        total_hours = round(total_minutes / 60, 2)
        average_session_length = round(total_minutes / total_sessions, 1) if total_sessions else 0

        return {
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "total_hours": total_hours,
            "unique_patients": len(unique_patients),
            "average_session_length": average_session_length,
            "first_session": first_session.isoformat() if first_session else None,
            "last_session": last_session.isoformat() if last_session else None,
            "by_day": by_day,
            "by_discipline": by_discipline,
        }

    def list_open_sessions(self):
        return (
            self.db.query(SessionModel)
            .filter(SessionModel.therapist_id == None)  # noqa: E711
            .filter(SessionModel.status != "canceled")
            .filter(SessionModel.status != "completed")
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

    def complete_session(self, session_id: str, notes: str | None = None):
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        old_values = {
            "status": session.status,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }

        session.status = "completed"
        session.completed_at = datetime.utcnow()
        if notes is not None:
            session.notes = notes

        self.db.commit()
        self.db.refresh(session)

        new_values = {
            "status": session.status,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }

        audit_service = SessionAuditService(self.db)
        audit_service.log_action(
            session_id=session_id,
            action_type="completed",
            performed_by="system:auto",
            old_values=old_values,
            new_values=new_values,
            notes=f"Session marked as completed" + (f"; notes updated: {notes}" if notes else ""),
        )

        # Notify therapist and family
        notification_service = NotificationService(self.db)
        if session.therapist_id:
            notification_service.notify_therapist(
                session.therapist_id,
                session_id,
                "SESSION_COMPLETED",
                f"Session for patient {session.patient_id} on {session.date.isoformat()} has been marked as completed.",
            )
        notification_service.notify_family(
            session.patient_id,
            session_id,
            "SESSION_COMPLETED",
            f"Your therapy session on {session.date.isoformat()} ({session.discipline}) has been completed.",
        )

        return self._serialize_session(session)

    def cancel_session(self, session_id: str, reason: str | None = None):
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        old_values = {
            "status": session.status,
            "therapist_id": session.therapist_id,
            "canceled_at": session.canceled_at.isoformat() if session.canceled_at else None,
            "cancellation_reason": session.cancellation_reason,
        }

        session.status = "canceled"
        session.canceled_at = datetime.utcnow()
        session.cancellation_reason = reason
        session.therapist_id = None

        self.db.commit()
        self.db.refresh(session)

        new_values = {
            "status": session.status,
            "therapist_id": session.therapist_id,
            "canceled_at": session.canceled_at.isoformat() if session.canceled_at else None,
            "cancellation_reason": session.cancellation_reason,
        }

        audit_service = SessionAuditService(self.db)
        audit_service.log_action(
            session_id=session_id,
            action_type="canceled",
            performed_by="system:auto",
            old_values=old_values,
            new_values=new_values,
            notes=f"Session canceled" + (f"; reason: {reason}" if reason else ""),
        )

        # Notify therapist (if was assigned) and family
        notification_service = NotificationService(self.db)
        if old_values["therapist_id"]:
            notification_service.notify_therapist(
                old_values["therapist_id"],
                session_id,
                "SESSION_CANCELED",
                f"Your session for patient {session.patient_id} on {session.date.isoformat()} has been canceled. Reason: {reason or 'No reason provided'}",
            )
        notification_service.notify_family(
            session.patient_id,
            session_id,
            "SESSION_CANCELED",
            f"Your therapy session on {session.date.isoformat()} ({session.discipline}) has been canceled. Reason: {reason or 'No reason provided'}",
        )

        return self._serialize_session(session)

    def reschedule_session(self, session_id: str, date_value, start_time_value, end_time_value):
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        try:
            new_date = self._parse_date(date_value)
            new_start = self._parse_time(start_time_value)
            new_end = self._parse_time(end_time_value)
        except ValueError as exc:
            return {
                "success": False,
                "reason": str(exc),
                "conflicts": [],
            }

        if new_start >= new_end:
            return {
                "success": False,
                "reason": "start_time must be before end_time",
                "conflicts": [],
            }

        original_date = session.date
        original_start = session.start_time
        original_end = session.end_time

        session.date = new_date
        session.start_time = new_start
        session.end_time = new_end

        if session.therapist_id:
            conflict_service = ConflictDetectionService(self.db)
            report = conflict_service.detect_conflicts_for_session(session_id)
            if report and report["has_conflicts"]:
                session.date = original_date
                session.start_time = original_start
                session.end_time = original_end
                self.db.expire(session)
                return {
                    "success": False,
                    "conflicts": report["conflicts"],
                }

        if session.status == "canceled":
            session.status = "unassigned" if session.therapist_id is None else "scheduled"

        old_values = {
            "date": original_date.isoformat(),
            "start_time": original_start.isoformat(),
            "end_time": original_end.isoformat(),
        }

        self.db.commit()
        self.db.refresh(session)

        new_values = {
            "date": session.date.isoformat(),
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat(),
        }

        audit_service = SessionAuditService(self.db)
        audit_service.log_action(
            session_id=session_id,
            action_type="rescheduled",
            performed_by="system:auto",
            old_values=old_values,
            new_values=new_values,
            notes="Session date/time updated",
        )

        # Notify therapist and family
        notification_service = NotificationService(self.db)
        if session.therapist_id:
            notification_service.notify_therapist(
                session.therapist_id,
                session_id,
                "SESSION_RESCHEDULED",
                f"Your session for patient {session.patient_id} has been rescheduled to {session.date.isoformat()} from {session.start_time.isoformat()} to {session.end_time.isoformat()}.",
            )
        notification_service.notify_family(
            session.patient_id,
            session_id,
            "SESSION_RESCHEDULED",
            f"Your therapy session has been rescheduled to {session.date.isoformat()} from {session.start_time.isoformat()} to {session.end_time.isoformat()}.",
        )

        return {
            "success": True,
            "session": self._serialize_session(session),
        }

    def request_shift_pickup(self, session_id: str, therapist_id: str):
        session = self.get_session_by_id(session_id)
        if not session:
            return None

        if session.therapist_id is not None:
            return {
                "success": False,
                "error": "Session is already assigned to a therapist",
                "conflicts": [],
            }

        therapist = (
            self.db.query(Therapist)
            .filter(Therapist.therapist_id == therapist_id)
            .first()
        )
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found",
                "conflicts": [],
            }

        # Temporarily assign therapist so conflict detection can run the full check
        session.therapist_id = therapist_id
        conflict_service = ConflictDetectionService(self.db)
        report = conflict_service.detect_conflicts_for_session(session_id)

        if report["has_conflicts"]:
            # Roll back the assignment
            session.therapist_id = None
            self.db.expire(session)
            return {
                "success": False,
                "error": "Conflicts detected",
                "conflicts": report["conflicts"],
            }

        session.status = "scheduled"
        self.db.commit()
        self.db.refresh(session)

        audit_service = SessionAuditService(self.db)
        audit_service.log_action(
            session_id=session_id,
            action_type="assigned",
            performed_by=f"therapist:{therapist_id}",
            old_values={"therapist_id": None, "status": "unassigned"},
            new_values={"therapist_id": therapist_id, "status": session.status},
            notes="Therapist picked up open session",
        )

        # Notify family of assignment
        notification_service = NotificationService(self.db)
        notification_service.notify_family(
            session.patient_id,
            session_id,
            "SESSION_ASSIGNED",
            f"A therapist has been assigned to your {session.discipline} session on {session.date.isoformat()} from {session.start_time.isoformat()} to {session.end_time.isoformat()}.",
        )

        return {
            "success": True,
            "session": self._serialize_session(session),
        }

    def delete_session(self, session_id: str):
        session = self.get_session_by_id(session_id)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        return True