from datetime import datetime, timedelta
from sqlalchemy.orm import Session as OrmSession
from backend.app.models.session import Session as SessionModel
from backend.app.models.therapist import Therapist
from backend.app.models.therapist_availability import TherapistAvailability, TherapistTimeOff
from backend.app.services.conflict_detection_service import ConflictDetectionService
from backend.app.services.session_audit_service import SessionAuditService
from backend.app.services.notification_service import NotificationService

WEEKLY_LOAD_CAP = 20  # used to normalise weekly load score
DISCIPLINE_PRIORITY = {
    "PT": 0,
    "OT": 1,
    "ST": 2,
}


class MatchingService:
    def __init__(self, db: OrmSession):
        self.db = db
        self._conflict_service = ConflictDetectionService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _duration_minutes(self, start_time, end_time, ref_date):
        start_dt = datetime.combine(ref_date, start_time)
        end_dt = datetime.combine(ref_date, end_time)
        return int((end_dt - start_dt).total_seconds() / 60)

    def _overlaps(self, a_start, a_end, b_start, b_end):
        """Return True if two half-open intervals [a_start, a_end) and [b_start, b_end) overlap."""
        return a_start < b_end and a_end > b_start

    def _discipline_priority(self, discipline):
        return DISCIPLINE_PRIORITY.get((discipline or "").upper(), 99)

    # ------------------------------------------------------------------
    # Hard filters
    # ------------------------------------------------------------------

    def _passes_availability(self, therapist_id, session_dow, session_start, session_end):
        """Return the covering availability block, or None if no block covers the session window."""
        blocks = (
            self.db.query(TherapistAvailability)
            .filter(
                TherapistAvailability.therapist_id == therapist_id,
                TherapistAvailability.day_of_week == session_dow,
            )
            .all()
        )
        for block in blocks:
            if block.start_time <= session_start and block.end_time >= session_end:
                return block
        return None

    def _has_time_off(self, therapist_id, session_datetime_start, session_datetime_end):
        blocks = (
            self.db.query(TherapistTimeOff)
            .filter(TherapistTimeOff.therapist_id == therapist_id)
            .all()
        )
        return any(
            self._overlaps(
                block.start_datetime, block.end_datetime,
                session_datetime_start, session_datetime_end,
            )
            for block in blocks
        )

    def _has_schedule_conflict(self, therapist_id, session_date, session_start, session_end, exclude_session_id):
        existing = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date == session_date,
                SessionModel.id != exclude_session_id,
            )
            .all()
        )
        return (
            existing,
            any(
                self._overlaps(s.start_time, s.end_time, session_start, session_end)
                for s in existing
            ),
        )

    def _exceeds_daily_limits(self, covering_block, existing_sessions, session_date, session_start, session_end):
        """Return True if adding the new session would exceed max_sessions or max_minutes."""
        if covering_block.max_sessions is not None:
            if len(existing_sessions) >= covering_block.max_sessions:
                return True
        if covering_block.max_minutes is not None:
            current_minutes = sum(
                self._duration_minutes(s.start_time, s.end_time, session_date)
                for s in existing_sessions
            )
            new_minutes = self._duration_minutes(session_start, session_end, session_date)
            if current_minutes + new_minutes > covering_block.max_minutes:
                return True
        return False

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_therapist(
        self,
        therapist,
        session,
        covering_block,
        existing_day_sessions,
    ):
        score = 0
        reasons = []

        # 1. Discipline match — primary specialty aligns with session (30 pts)
        #    All candidates have passed the hard discipline filter so they match;
        #    give the full 30 pts as baseline.
        score += 30
        reasons.append("discipline_match")

        # 2. Seen patient before (25 pts)
        prior = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist.therapist_id,
                SessionModel.patient_id == session.patient_id,
                SessionModel.id != session.id,
            )
            .first()
        )
        if prior:
            score += 25
            reasons.append("seen_patient_before")

        # 3. Weekly load — lower load = higher score (25 pts)
        week_start = session.date - timedelta(days=session.date.weekday())
        week_end = week_start + timedelta(days=6)
        weekly_count = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist.therapist_id,
                SessionModel.date >= week_start,
                SessionModel.date <= week_end,
                SessionModel.id != session.id,
            )
            .count()
        )
        load_ratio = min(weekly_count / WEEKLY_LOAD_CAP, 1.0)
        load_score = round((1.0 - load_ratio) * 25)
        score += load_score

        # 4. Proximity — how well the session fits within the availability window (20 pts)
        #    Sessions that consume a moderate portion of the window score higher;
        #    penalise very tight fits (utilisation > 0.9) and very loose fits (< 0.1).
        session_mins = self._duration_minutes(session.start_time, session.end_time, session.date)
        block_mins = self._duration_minutes(covering_block.start_time, covering_block.end_time, session.date)
        if block_mins > 0:
            utilisation = session_mins / block_mins
            proximity_score = round((1.0 - abs(utilisation - 0.5)) * 20)
        else:
            proximity_score = 10
        score += proximity_score

        return score, reasons, weekly_count

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def match_therapists_to_session(self, session_id: str):
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return None

        session_dow = session.date.weekday()
        session_datetime_start = datetime.combine(session.date, session.start_time)
        session_datetime_end = datetime.combine(session.date, session.end_time)

        therapists = (
            self.db.query(Therapist)
            .filter(Therapist.active == True)
            .all()
        )

        candidates = []

        for therapist in therapists:
            t_id = therapist.therapist_id

            # Hard filter: discipline
            if therapist.discipline != session.discipline:
                continue

            # Hard filter: all conflict checks via ConflictDetectionService
            if self._conflict_service.has_any_conflict(t_id, session):
                continue

            # Score (availability block still needed for proximity scoring)
            covering_block = self._passes_availability(
                t_id, session_dow, session.start_time, session.end_time
            )
            existing_day_sessions, _ = self._has_schedule_conflict(
                t_id, session.date, session.start_time, session.end_time, session_id
            )

            # Score
            score, reasons, weekly_count = self._score_therapist(
                therapist, session, covering_block, existing_day_sessions
            )

            candidates.append({
                "therapist_id": t_id,
                "first_name": therapist.first_name,
                "last_name": therapist.last_name,
                "discipline": therapist.discipline,
                "score": score,
                "score_reasons": reasons,
                "weekly_sessions": weekly_count,
                "daily_sessions_on_date": len(existing_day_sessions),
            })

        candidates.sort(key=lambda c: c["score"], reverse=True)

        return {
            "best_match": candidates[0] if candidates else None,
            "alternatives": candidates[1:],
        }

    def auto_assign_session(self, session_id: str, dry_run: bool = False):
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return None

        if session.status in {"completed", "canceled"}:
            return {
                "success": False,
                "reason": f"Session cannot be auto-assigned when status is '{session.status}'",
                "alternatives": [],
            }

        if session.therapist_id is not None:
            return {
                "success": False,
                "reason": "Session is already assigned",
                "alternatives": [],
            }

        match_result = self.match_therapists_to_session(session_id)
        if not match_result:
            return {
                "success": False,
                "reason": "No eligible therapists",
                "alternatives": [],
            }

        ranked = ([match_result["best_match"]] if match_result["best_match"] else []) + match_result["alternatives"]

        for candidate in ranked:
            t_id = candidate["therapist_id"]

            # Temporarily assign to run full conflict detection
            session.therapist_id = t_id
            report = self._conflict_service.detect_conflicts_for_session(session_id)

            if not report["has_conflicts"]:
                if dry_run:
                    session.therapist_id = None
                    self.db.expire(session)
                    return {
                        "success": True,
                        "assigned_to": t_id,
                        "score": candidate["score"],
                        "session_id": session_id,
                        "dry_run": True,
                    }
                session.status = "scheduled"
                self.db.commit()
                self.db.refresh(session)

                # Log audit entry
                audit_service = SessionAuditService(self.db)
                audit_service.log_action(
                    session_id=session_id,
                    action_type="assigned",
                    performed_by="system:auto",
                    old_values={"therapist_id": None, "status": "unassigned"},
                    new_values={"therapist_id": t_id, "status": session.status},
                    notes=f"Auto-assigned to therapist {t_id} (score: {candidate['score']})",
                )

                # Send notifications
                notification_service = NotificationService(self.db)
                notification_service.notify_therapist(
                    t_id,
                    session_id,
                    "SESSION_ASSIGNED",
                    f"You have been assigned a {session.discipline} session for patient {session.patient_id} on {session.date.isoformat()} from {session.start_time.isoformat()} to {session.end_time.isoformat()}.",
                )
                notification_service.notify_family(
                    session.patient_id,
                    session_id,
                    "SESSION_ASSIGNED",
                    f"A therapist has been assigned to your {session.discipline} session on {session.date.isoformat()} from {session.start_time.isoformat()} to {session.end_time.isoformat()}.",
                )

                return {
                    "success": True,
                    "assigned_to": t_id,
                    "score": candidate["score"],
                    "session_id": session_id,
                }

            # Roll back and try the next candidate
            session.therapist_id = None
            self.db.expire(session)

        return {
            "success": False,
            "reason": "No eligible therapists",
            "alternatives": ranked,
        }

    def bulk_auto_assign(self, dry_run: bool = False):
        open_sessions = (
            self.db.query(SessionModel)
            .filter(SessionModel.therapist_id == None)
            .filter(SessionModel.status != "canceled")
            .filter(SessionModel.status != "completed")
            .all()
        )

        sorted_sessions = sorted(
            open_sessions,
            key=lambda s: (
                s.date,
                self._discipline_priority(s.discipline),
                -self._duration_minutes(s.start_time, s.end_time, s.date),
            ),
        )

        assigned = []
        failed = []

        for session in sorted_sessions:
            duration_minutes = self._duration_minutes(session.start_time, session.end_time, session.date)
            result = self.auto_assign_session(session.id, dry_run=dry_run)

            if result and result.get("success"):
                assigned.append({
                    "session_id": session.id,
                    "date": session.date.isoformat(),
                    "discipline": session.discipline,
                    "duration_minutes": duration_minutes,
                    "assigned_to": result.get("assigned_to"),
                    "score": result.get("score"),
                    "dry_run": dry_run,
                })
                continue

            failed.append({
                "session_id": session.id,
                "date": session.date.isoformat(),
                "discipline": session.discipline,
                "duration_minutes": duration_minutes,
                "reason": (result or {}).get("reason", "Session not found"),
                "alternatives": (result or {}).get("alternatives", []),
                "dry_run": dry_run,
            })

        return {
            "dry_run": dry_run,
            "total_open_sessions": len(sorted_sessions),
            "assigned": assigned,
            "failed": failed,
        }

    def smart_reschedule_session(self, session_id: str):
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return None

        if session.status in {"completed", "canceled"}:
            return {
                "success": False,
                "reason": f"Session cannot be smart-rescheduled when status is '{session.status}'",
                "previous_therapist_id": session.therapist_id,
                "alternatives": [],
            }

        # Release the current assignment so matching considers the full pool
        previous_therapist_id = session.therapist_id
        session.therapist_id = None

        match_result = self.match_therapists_to_session(session_id)
        if not match_result:
            # Restore original assignment and report failure
            session.therapist_id = previous_therapist_id
            return {
                "success": False,
                "reason": "No eligible therapists",
                "previous_therapist_id": previous_therapist_id,
                "alternatives": [],
            }

        ranked = ([match_result["best_match"]] if match_result["best_match"] else []) + match_result["alternatives"]

        for candidate in ranked:
            t_id = candidate["therapist_id"]

            # Temporarily assign to run full conflict detection
            session.therapist_id = t_id
            report = self._conflict_service.detect_conflicts_for_session(session_id)

            if not report["has_conflicts"]:
                session.status = "scheduled"
                self.db.commit()
                self.db.refresh(session)

                # Log audit entry
                audit_service = SessionAuditService(self.db)
                audit_service.log_action(
                    session_id=session_id,
                    action_type="smart_rescheduled",
                    performed_by="system:auto",
                    old_values={"therapist_id": previous_therapist_id, "status": "scheduled"},
                    new_values={"therapist_id": t_id, "status": session.status},
                    notes=f"Smart-rescheduled from {previous_therapist_id} to {t_id} (score: {candidate['score']})",
                )

                # Send notifications
                notification_service = NotificationService(self.db)
                # Notify old therapist of unassignment
                notification_service.notify_therapist(
                    previous_therapist_id,
                    session_id,
                    "SESSION_REASSIGNED",
                    f"Your session for patient {session.patient_id} on {session.date.isoformat()} has been reassigned to another therapist.",
                )
                # Notify new therapist of assignment
                notification_service.notify_therapist(
                    t_id,
                    session_id,
                    "SESSION_ASSIGNED",
                    f"You have been assigned a {session.discipline} session for patient {session.patient_id} on {session.date.isoformat()} from {session.start_time.isoformat()} to {session.end_time.isoformat()}.",
                )
                # Notify family of reassignment
                notification_service.notify_family(
                    session.patient_id,
                    session_id,
                    "SESSION_REASSIGNED",
                    f"Your {session.discipline} session on {session.date.isoformat()} has been reassigned to a different therapist.",
                )

                return {
                    "success": True,
                    "assigned_to": t_id,
                    "previous_therapist_id": previous_therapist_id,
                    "score": candidate["score"],
                    "session_id": session_id,
                }

            # Roll back and try the next candidate
            session.therapist_id = None
            self.db.expire(session)

        # All candidates failed — restore original assignment
        session.therapist_id = previous_therapist_id
        self.db.commit()
        return {
            "success": False,
            "reason": "No eligible therapists",
            "previous_therapist_id": previous_therapist_id,
            "alternatives": ranked,
        }
