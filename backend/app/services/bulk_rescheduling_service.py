from datetime import datetime
from sqlalchemy.orm import Session as OrmSession

from app.models.session import Session as SessionModel
from app.services.conflict_detection_service import ConflictDetectionService
from app.services.matching_service import MatchingService
from app.services.notification_service import NotificationService
from app.services.session_audit_service import SessionAuditService
from app.services.session_service import SessionService
from app.services.therapist_service import TherapistService


class BulkReschedulingService:
    def __init__(self, db: OrmSession):
        self.db = db
        self.session_service = SessionService(db)
        self.therapist_service = TherapistService(db)
        self.matching_service = MatchingService(db)
        self.conflict_service = ConflictDetectionService(db)
        self.notification_service = NotificationService(db)
        self.audit_service = SessionAuditService(db)

    def _assign_best_candidate(self, session_id: str, excluded_therapist_id: str | None = None) -> dict:
        match_result = self.matching_service.match_therapists_to_session(session_id)
        if not match_result:
            return {
                "success": False,
                "reason": "No eligible therapists",
                "alternatives": [],
            }

        ranked = []
        if match_result.get("best_match"):
            ranked.append(match_result["best_match"])
        ranked.extend(match_result.get("alternatives", []))

        if excluded_therapist_id:
            ranked = [c for c in ranked if c.get("therapist_id") != excluded_therapist_id]

        if not ranked:
            return {
                "success": False,
                "reason": "No alternate therapists available",
                "alternatives": [],
            }

        session = self.session_service.get_session_by_id(session_id)
        if not session:
            return {
                "success": False,
                "reason": "Session not found",
                "alternatives": [],
            }

        for candidate in ranked:
            therapist_id = candidate["therapist_id"]

            session.therapist_id = therapist_id
            conflict_report = self.conflict_service.detect_conflicts_for_session(session_id)

            if conflict_report and not conflict_report.get("has_conflicts"):
                session.status = "scheduled"
                self.db.commit()
                self.db.refresh(session)

                return {
                    "success": True,
                    "assigned_to": therapist_id,
                    "score": candidate.get("score"),
                }

            session.therapist_id = None
            self.db.expire(session)

        return {
            "success": False,
            "reason": "No conflict-free therapist candidates",
            "alternatives": ranked,
        }

    def bulk_reschedule(self, therapist_id: str, start_date, end_date) -> dict:
        therapist = self.therapist_service.get_therapist_by_id(therapist_id)
        if not therapist:
            return {
                "success": False,
                "error": "Therapist not found",
            }

        sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date >= start_date,
                SessionModel.date <= end_date,
            )
            .order_by(SessionModel.date.asc(), SessionModel.start_time.asc())
            .all()
        )

        success_count = 0
        failures = []

        for session in sessions:
            if session.status in {"completed", "canceled"}:
                failures.append(
                    {
                        "session_id": session.id,
                        "reason": f"Session status '{session.status}' cannot be bulk rescheduled",
                    }
                )
                continue

            old_values = {
                "therapist_id": session.therapist_id,
                "status": session.status,
                "date": session.date.isoformat(),
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat(),
            }

            session.therapist_id = None
            session.status = "unassigned"
            self.db.commit()
            self.db.refresh(session)

            self.audit_service.log_action(
                session_id=session.id,
                action_type="bulk_unassigned",
                performed_by="system:bulk_rescheduler",
                old_values=old_values,
                new_values={
                    "therapist_id": session.therapist_id,
                    "status": session.status,
                },
                notes=(
                    f"Bulk reschedule release from therapist {therapist_id} "
                    f"for range {start_date.isoformat()} to {end_date.isoformat()}"
                ),
            )

            reassignment = self._assign_best_candidate(session.id, excluded_therapist_id=therapist_id)
            if not reassignment.get("success"):
                failures.append(
                    {
                        "session_id": session.id,
                        "reason": reassignment.get("reason", "Reassignment failed"),
                        "alternatives": reassignment.get("alternatives", []),
                    }
                )
                continue

            assigned_to = reassignment["assigned_to"]
            refreshed = self.session_service.get_session_by_id(session.id)

            self.audit_service.log_action(
                session_id=session.id,
                action_type="bulk_reassigned",
                performed_by="system:bulk_rescheduler",
                old_values={"therapist_id": None, "status": "unassigned"},
                new_values={"therapist_id": assigned_to, "status": refreshed.status},
                notes=f"Session reassigned during bulk reschedule; candidate score={reassignment.get('score')}",
            )

            self.notification_service.notify_therapist(
                assigned_to,
                session.id,
                "SESSION_ASSIGNED",
                (
                    f"You have been assigned a {refreshed.discipline} session for patient "
                    f"{refreshed.patient_id} on {refreshed.date.isoformat()} from "
                    f"{refreshed.start_time.isoformat()} to {refreshed.end_time.isoformat()} "
                    f"via bulk rescheduling."
                ),
            )
            self.notification_service.notify_family(
                refreshed.patient_id,
                session.id,
                "SESSION_ASSIGNED",
                (
                    f"Your {refreshed.discipline} session on {refreshed.date.isoformat()} from "
                    f"{refreshed.start_time.isoformat()} to {refreshed.end_time.isoformat()} "
                    f"has been reassigned to a new therapist."
                ),
            )

            success_count += 1

        return {
            "therapist_id": therapist_id,
            "range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "generated_at": datetime.utcnow().isoformat(),
            "sessions_processed": len(sessions),
            "successfully_reassigned": success_count,
            "failed": failures,
        }
