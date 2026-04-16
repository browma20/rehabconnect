"""
MarketplaceService
==================
Provides a multi-step pipeline for patient-side session requests:

  request_session  → create a pending (unassigned) session
  generate_candidates → hard-filter eligible therapists
  score_therapists    → weighted scoring of each candidate
  auto_assign_best    → assign if top score exceeds threshold,
                        otherwise surface the ranked list for manual review

Scoring weights (sum = 1.0)
  availability_score    0.25  – does the therapist cover the exact slot?
  performance_score     0.30  – historical utilisation rate (0–100 mapped)
  reliability_score     0.30  – audit-derived reliability score (0–100)
  caseload_balance_score 0.15 – inverse of current weekly workload
"""

import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session as OrmSession

from app.models.patient import Patient as PatientModel
from app.models.session import Session as SessionModel
from app.models.therapist import Therapist as TherapistModel
from app.models.therapist_availability import TherapistAvailability, TherapistTimeOff
from app.services.conflict_detection_service import ConflictDetectionService
from app.services.notification_service import NotificationService
from app.services.session_audit_service import SessionAuditService
from app.services.therapist_analytics_service import TherapistAnalyticsService

# -----------------------------------------------------------------------
# Tunable constants – change these to re-tune without touching logic
# -----------------------------------------------------------------------
WEIGHTS = {
    "availability": 0.25,
    "performance": 0.30,
    "reliability": 0.30,
    "caseload_balance": 0.15,
}
WEEKLY_LOAD_CAP = 20          # sessions per week considered "full"
AUTO_ASSIGN_THRESHOLD = 40.0  # composite score (0–100) required for auto-assign
LOOKBACK_WEEKS = 8            # weeks of history for analytics


class MarketplaceService:
    def __init__(self, db: OrmSession):
        self.db = db
        self._conflict_service = ConflictDetectionService(db)
        self._analytics = TherapistAnalyticsService(db)
        self._audit = SessionAuditService(db)
        self._notifications = NotificationService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_date(self, value) -> date:
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    def _parse_time(self, value) -> time:
        if isinstance(value, time):
            return value
        return time.fromisoformat(str(value))

    def _week_monday(self, value: date) -> date:
        return value - timedelta(days=value.weekday())

    def _duration_minutes(self, start: time, end: time, ref: date) -> int:
        return max(
            0,
            int(
                (datetime.combine(ref, end) - datetime.combine(ref, start)).total_seconds()
                / 60
            ),
        )

    def _has_time_off(self, therapist_id: str, session_date: date,
                      session_start: time, session_end: time) -> bool:
        s_start = datetime.combine(session_date, session_start)
        s_end = datetime.combine(session_date, session_end)
        return (
            self.db.query(TherapistTimeOff)
            .filter(
                TherapistTimeOff.therapist_id == therapist_id,
                TherapistTimeOff.start_datetime < s_end,
                TherapistTimeOff.end_datetime > s_start,
            )
            .first()
            is not None
        )

    def _covering_block(
        self, therapist_id: str, day_of_week: int, start: time, end: time
    ):
        blocks = (
            self.db.query(TherapistAvailability)
            .filter(
                TherapistAvailability.therapist_id == therapist_id,
                TherapistAvailability.day_of_week == day_of_week,
            )
            .all()
        )
        for b in blocks:
            if b.start_time <= start and b.end_time >= end:
                return b
        return None

    def _weekly_session_count(self, therapist_id: str, ref_date: date) -> int:
        week_start = self._week_monday(ref_date)
        week_end = week_start + timedelta(days=6)
        return (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date >= week_start,
                SessionModel.date <= week_end,
                SessionModel.status != "canceled",
            )
            .count()
        )

    def _analytics_scores(self, therapist_id: str) -> tuple[float, float]:
        """Return (utilization_rate 0–1, reliability_score 0–100)."""
        today = date.today()
        lookback_start = self._week_monday(today) - timedelta(days=7 * LOOKBACK_WEEKS)
        lookback_end = today
        result = self._analytics.get_productivity(therapist_id, lookback_start, lookback_end)
        if result.get("success"):
            return (
                result["metrics"]["utilization_rate"],
                result["audit_insights"]["reliability_score"],
            )
        return 1.0, 100.0

    # ------------------------------------------------------------------
    # Sub-scorers (each returns 0–100)
    # ------------------------------------------------------------------

    def _score_availability(
        self, therapist_id: str, session_date: date, start: time, end: time
    ) -> float:
        block = self._covering_block(therapist_id, session_date.weekday(), start, end)
        if not block:
            return 0.0

        # Bonus: how comfortably does the session fit inside the window?
        session_mins = self._duration_minutes(start, end, session_date)
        block_mins = self._duration_minutes(block.start_time, block.end_time, session_date)
        if block_mins <= 0:
            return 50.0
        utilisation = session_mins / block_mins
        # Peak at 50 % utilisation; fade toward each extreme
        proximity = (1.0 - abs(utilisation - 0.5)) * 100.0
        return round(min(100.0, max(0.0, proximity)), 2)

    def _score_performance(self, therapist_id: str) -> float:
        utilization_rate, _ = self._analytics_scores(therapist_id)
        return round(min(100.0, utilization_rate * 100.0), 2)

    def _score_reliability(self, therapist_id: str) -> float:
        _, reliability_score = self._analytics_scores(therapist_id)
        return round(min(100.0, max(0.0, reliability_score)), 2)

    def _score_caseload(self, therapist_id: str, session_date: date) -> float:
        weekly = self._weekly_session_count(therapist_id, session_date)
        load_ratio = min(weekly / WEEKLY_LOAD_CAP, 1.0)
        return round((1.0 - load_ratio) * 100.0, 2)

    def _composite_score(
        self,
        availability: float,
        performance: float,
        reliability: float,
        caseload: float,
    ) -> float:
        return round(
            availability * WEIGHTS["availability"]
            + performance * WEIGHTS["performance"]
            + reliability * WEIGHTS["reliability"]
            + caseload * WEIGHTS["caseload_balance"],
            2,
        )

    # ------------------------------------------------------------------
    # Public pipeline methods
    # ------------------------------------------------------------------

    def request_session(
        self,
        patient_id: str,
        discipline: str,
        preferred_times: list,
        duration: int | None = None,
        recurrence: str | None = None,
    ) -> dict:
        """
        Create a pending (unassigned) session from the first valid preferred slot.

        preferred_times: list of dicts with keys date, start_time, end_time.
        recurrence:      optional human-readable label ("weekly", "daily", etc.)
                         stored in session notes; the caller is responsible for
                         submitting a separate request for each recurrence instance.
        """
        patient = (
            self.db.query(PatientModel)
            .filter(PatientModel.patient_id == patient_id)
            .first()
        )
        if not patient:
            return {"success": False, "error": "Patient not found"}

        discipline = discipline.upper()

        if not preferred_times:
            return {"success": False, "error": "At least one preferred_time is required"}

        # Use the first preferred slot to create the actual session
        slot = preferred_times[0]
        try:
            session_date = self._parse_date(slot["date"])
            start = self._parse_time(slot["start_time"])
            end = self._parse_time(slot["end_time"])
        except (KeyError, ValueError) as exc:
            return {
                "success": False,
                "error": f"Invalid preferred_time entry: {exc!s}",
            }

        if start >= end:
            return {"success": False, "error": "start_time must be before end_time"}

        notes_parts = []
        if recurrence:
            notes_parts.append(f"Recurrence: {recurrence}")
        if len(preferred_times) > 1:
            notes_parts.append(
                f"Alternate preferred slots: "
                + "; ".join(
                    f"{s.get('date')} {s.get('start_time')}–{s.get('end_time')}"
                    for s in preferred_times[1:]
                )
            )

        session = SessionModel(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            discipline=discipline,
            date=session_date,
            start_time=start,
            end_time=end,
            status="unassigned",
            therapist_id=None,
            notes="; ".join(notes_parts) if notes_parts else None,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        self._audit.log_action(
            session_id=session.id,
            action_type="created",
            performed_by=f"family:{patient_id}",
            old_values=None,
            new_values={
                "patient_id": patient_id,
                "discipline": discipline,
                "date": session_date.isoformat(),
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "status": "unassigned",
            },
            notes="Session request submitted via marketplace",
        )

        return {
            "success": True,
            "session_id": session.id,
            "session": {
                "id": session.id,
                "patient_id": session.patient_id,
                "discipline": session.discipline,
                "date": session.date.isoformat(),
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat(),
                "status": session.status,
                "notes": session.notes,
            },
        }

    def generate_candidates(self, session_id: str) -> dict:
        """
        Return all therapists who are eligible for the given session
        after applying discipline, availability, time-off and conflict filters.
        """
        session = (
            self.db.query(SessionModel)
            .filter(SessionModel.id == session_id)
            .first()
        )
        if not session:
            return {"success": False, "error": "Session not found"}

        therapists = (
            self.db.query(TherapistModel)
            .filter(
                TherapistModel.active == True,
                TherapistModel.discipline == session.discipline,
            )
            .all()
        )

        eligible = []
        for t in therapists:
            if self._has_time_off(t.therapist_id, session.date, session.start_time, session.end_time):
                continue
            if not self._covering_block(t.therapist_id, session.date.weekday(), session.start_time, session.end_time):
                continue
            # Full conflict check – temporarily assign for the detector, then roll back
            original_therapist = session.therapist_id
            session.therapist_id = t.therapist_id
            conflict_report = self._conflict_service.detect_conflicts_for_session(session_id)
            session.therapist_id = original_therapist
            self.db.expire(session)
            if conflict_report and conflict_report.get("has_conflicts"):
                continue
            eligible.append(t)

        return {
            "success": True,
            "session_id": session_id,
            "discipline": session.discipline,
            "date": session.date.isoformat(),
            "candidates": [
                {
                    "therapist_id": t.therapist_id,
                    "name": f"{t.first_name} {t.last_name}",
                    "discipline": t.discipline,
                }
                for t in eligible
            ],
            "count": len(eligible),
        }

    def score_therapists(self, session_id: str, candidate_ids: list[str] | None = None) -> dict:
        """
        Score every eligible therapist (or a subset supplied via candidate_ids).
        Returns a ranked list with per-dimension breakdowns.
        """
        session = (
            self.db.query(SessionModel)
            .filter(SessionModel.id == session_id)
            .first()
        )
        if not session:
            return {"success": False, "error": "Session not found"}

        if candidate_ids is None:
            gen = self.generate_candidates(session_id)
            if not gen.get("success"):
                return gen
            candidate_ids = [c["therapist_id"] for c in gen["candidates"]]

        ranked = []
        for t_id in candidate_ids:
            therapist = (
                self.db.query(TherapistModel)
                .filter(TherapistModel.therapist_id == t_id)
                .first()
            )
            if not therapist:
                continue

            avail = self._score_availability(t_id, session.date, session.start_time, session.end_time)
            perf = self._score_performance(t_id)
            rel = self._score_reliability(t_id)
            caseload = self._score_caseload(t_id, session.date)
            composite = self._composite_score(avail, perf, rel, caseload)

            ranked.append(
                {
                    "therapist_id": t_id,
                    "name": f"{therapist.first_name} {therapist.last_name}",
                    "discipline": therapist.discipline,
                    "composite_score": composite,
                    "score_breakdown": {
                        "availability_score": avail,
                        "performance_score": perf,
                        "reliability_score": rel,
                        "caseload_balance_score": caseload,
                        "weights": WEIGHTS,
                    },
                    "weekly_sessions": self._weekly_session_count(t_id, session.date),
                }
            )

        ranked.sort(key=lambda x: x["composite_score"], reverse=True)

        return {
            "success": True,
            "session_id": session_id,
            "scoring_weights": WEIGHTS,
            "auto_assign_threshold": AUTO_ASSIGN_THRESHOLD,
            "count": len(ranked),
            "ranked": ranked,
        }

    def auto_assign_best(
        self,
        session_id: str,
        threshold: float = AUTO_ASSIGN_THRESHOLD,
    ) -> dict:
        """
        If the top-scored eligible therapist meets the threshold, assign them.
        Otherwise return the ranked list for manual review.
        """
        session = (
            self.db.query(SessionModel)
            .filter(SessionModel.id == session_id)
            .first()
        )
        if not session:
            return {"success": False, "error": "Session not found"}

        if session.status in {"completed", "canceled"}:
            return {
                "success": False,
                "error": f"Session status '{session.status}' cannot be auto-assigned",
            }
        if session.therapist_id is not None:
            return {"success": False, "error": "Session is already assigned"}

        scored = self.score_therapists(session_id)
        if not scored.get("success"):
            return scored

        if not scored["ranked"]:
            return {
                "success": False,
                "auto_assigned": False,
                "reason": "no_eligible_therapists",
                "ranked": [],
            }

        best = scored["ranked"][0]
        if best["composite_score"] < threshold:
            return {
                "success": True,
                "auto_assigned": False,
                "reason": "below_threshold",
                "threshold": threshold,
                "top_score": best["composite_score"],
                "ranked": scored["ranked"],
            }

        # Assign best candidate
        best_id = best["therapist_id"]
        session.therapist_id = best_id
        session.status = "scheduled"
        self.db.commit()
        self.db.refresh(session)

        self._audit.log_action(
            session_id=session_id,
            action_type="assigned",
            performed_by="system:marketplace",
            old_values={"therapist_id": None, "status": "unassigned"},
            new_values={"therapist_id": best_id, "status": "scheduled"},
            notes=(
                f"Marketplace auto-assign: therapist {best_id} "
                f"(composite score {best['composite_score']})"
            ),
        )

        self._notifications.notify_therapist(
            best_id,
            session_id,
            "SESSION_ASSIGNED",
            (
                f"You have been assigned a {session.discipline} session for patient "
                f"{session.patient_id} on {session.date.isoformat()} "
                f"from {session.start_time.isoformat()} to {session.end_time.isoformat()} "
                f"via the marketplace."
            ),
        )
        self._notifications.notify_family(
            session.patient_id,
            session_id,
            "SESSION_ASSIGNED",
            (
                f"Your {session.discipline} session on {session.date.isoformat()} "
                f"from {session.start_time.isoformat()} to {session.end_time.isoformat()} "
                f"has been assigned to a therapist."
            ),
        )

        return {
            "success": True,
            "auto_assigned": True,
            "session_id": session_id,
            "assigned_to": best_id,
            "composite_score": best["composite_score"],
            "score_breakdown": best["score_breakdown"],
            "alternatives": scored["ranked"][1:],
        }

    def confirm_assignment(self, session_id: str, therapist_id: str, confirmed_by: str = "scheduler") -> dict:
        """Manually assign a therapist chosen from the ranked list."""
        session = (
            self.db.query(SessionModel)
            .filter(SessionModel.id == session_id)
            .first()
        )
        if not session:
            return {"success": False, "error": "Session not found"}

        if session.status in {"completed", "canceled"}:
            return {
                "success": False,
                "error": f"Session status '{session.status}' cannot be assigned",
            }
        if session.therapist_id is not None and session.therapist_id != therapist_id:
            return {
                "success": False,
                "error": f"Session is already assigned to therapist {session.therapist_id}",
            }

        therapist = (
            self.db.query(TherapistModel)
            .filter(TherapistModel.therapist_id == therapist_id)
            .first()
        )
        if not therapist:
            return {"success": False, "error": "Therapist not found"}

        if not therapist.active:
            return {"success": False, "error": "Therapist is not active"}

        # Final conflict check before committing
        session.therapist_id = therapist_id
        conflict_report = self._conflict_service.detect_conflicts_for_session(session_id)
        if conflict_report and conflict_report.get("has_conflicts"):
            session.therapist_id = None
            self.db.expire(session)
            return {
                "success": False,
                "error": "Conflicts detected for this assignment",
                "conflicts": conflict_report["conflicts"],
            }

        session.status = "scheduled"
        self.db.commit()
        self.db.refresh(session)

        self._audit.log_action(
            session_id=session_id,
            action_type="assigned",
            performed_by=f"scheduler:{confirmed_by}",
            old_values={"therapist_id": None, "status": "unassigned"},
            new_values={"therapist_id": therapist_id, "status": "scheduled"},
            notes=f"Marketplace manual confirmation by {confirmed_by}",
        )

        self._notifications.notify_therapist(
            therapist_id,
            session_id,
            "SESSION_ASSIGNED",
            (
                f"You have been assigned a {session.discipline} session for patient "
                f"{session.patient_id} on {session.date.isoformat()} "
                f"from {session.start_time.isoformat()} to {session.end_time.isoformat()}."
            ),
        )
        self._notifications.notify_family(
            session.patient_id,
            session_id,
            "SESSION_ASSIGNED",
            (
                f"Your {session.discipline} session on {session.date.isoformat()} "
                f"from {session.start_time.isoformat()} to {session.end_time.isoformat()} "
                f"has been confirmed with a therapist."
            ),
        )

        return {
            "success": True,
            "session_id": session_id,
            "assigned_to": therapist_id,
            "therapist_name": f"{therapist.first_name} {therapist.last_name}",
            "confirmed_by": confirmed_by,
        }
