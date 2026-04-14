from datetime import datetime, timedelta
from sqlalchemy.orm import Session as OrmSession
from backend.app.models.session import Session as SessionModel
from backend.app.models.therapist import Therapist
from backend.app.models.therapist_availability import TherapistAvailability, TherapistTimeOff


class ConflictDetectionService:
    def __init__(self, db: OrmSession):
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _duration_minutes(self, start_time, end_time, ref_date):
        start_dt = datetime.combine(ref_date, start_time)
        end_dt = datetime.combine(ref_date, end_time)
        return int((end_dt - start_dt).total_seconds() / 60)

    def _overlaps(self, a_start, a_end, b_start, b_end):
        return a_start < b_end and a_end > b_start

    # ------------------------------------------------------------------
    # Individual conflict checks
    # ------------------------------------------------------------------

    def _check_time_overlap(self, therapist_id, session):
        conflicts = []
        others = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date == session.date,
                SessionModel.id != session.id,
            )
            .all()
        )
        for other in others:
            if self._overlaps(session.start_time, session.end_time, other.start_time, other.end_time):
                conflicts.append({
                    "type": "TIME_OVERLAP",
                    "detail": f"Overlaps session {other.id} ({other.start_time.isoformat()}–{other.end_time.isoformat()})",
                    "conflicting_session_id": other.id,
                })
        return conflicts

    def _check_outside_availability(self, therapist_id, session):
        dow = session.date.weekday()
        blocks = (
            self.db.query(TherapistAvailability)
            .filter(
                TherapistAvailability.therapist_id == therapist_id,
                TherapistAvailability.day_of_week == dow,
            )
            .all()
        )
        if not blocks:
            return [{
                "type": "OUTSIDE_AVAILABILITY",
                "detail": f"No availability block defined for day_of_week={dow}",
            }]
        covered = any(
            block.start_time <= session.start_time and block.end_time >= session.end_time
            for block in blocks
        )
        if not covered:
            return [{
                "type": "OUTSIDE_AVAILABILITY",
                "detail": (
                    f"Session {session.start_time.isoformat()}–{session.end_time.isoformat()} "
                    f"is not covered by any availability block on day_of_week={dow}"
                ),
            }]
        return []

    def _check_time_off(self, therapist_id, session):
        session_start = datetime.combine(session.date, session.start_time)
        session_end = datetime.combine(session.date, session.end_time)
        blocks = (
            self.db.query(TherapistTimeOff)
            .filter(TherapistTimeOff.therapist_id == therapist_id)
            .all()
        )
        conflicts = []
        for block in blocks:
            if self._overlaps(block.start_datetime, block.end_datetime, session_start, session_end):
                conflicts.append({
                    "type": "TIME_OFF",
                    "detail": (
                        f"Therapist is on time off from {block.start_datetime.isoformat()} "
                        f"to {block.end_datetime.isoformat()}"
                        + (f" ({block.reason})" if block.reason else "")
                    ),
                    "time_off_id": block.id,
                })
        return conflicts

    def _check_daily_load(self, therapist_id, session):
        dow = session.date.weekday()
        blocks = (
            self.db.query(TherapistAvailability)
            .filter(
                TherapistAvailability.therapist_id == therapist_id,
                TherapistAvailability.day_of_week == dow,
            )
            .all()
        )
        covering_block = next(
            (b for b in blocks if b.start_time <= session.start_time and b.end_time >= session.end_time),
            None,
        )
        if covering_block is None:
            return []

        existing = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date == session.date,
                SessionModel.id != session.id,
            )
            .all()
        )
        conflicts = []

        if covering_block.max_sessions is not None:
            if len(existing) >= covering_block.max_sessions:
                conflicts.append({
                    "type": "DAILY_LOAD",
                    "detail": (
                        f"Adding this session would exceed max_sessions={covering_block.max_sessions} "
                        f"for the day (currently {len(existing)})"
                    ),
                })

        if covering_block.max_minutes is not None:
            current_minutes = sum(
                self._duration_minutes(s.start_time, s.end_time, session.date) for s in existing
            )
            new_minutes = self._duration_minutes(session.start_time, session.end_time, session.date)
            if current_minutes + new_minutes > covering_block.max_minutes:
                conflicts.append({
                    "type": "DAILY_LOAD",
                    "detail": (
                        f"Adding this session ({new_minutes} min) would exceed max_minutes="
                        f"{covering_block.max_minutes} for the day (currently {current_minutes} min)"
                    ),
                })

        return conflicts

    def _check_weekly_load(self, therapist_id, session):
        week_start = session.date - timedelta(days=session.date.weekday())
        week_end = week_start + timedelta(days=6)

        # Collect all availability blocks that carry weekly caps
        blocks = (
            self.db.query(TherapistAvailability)
            .filter(TherapistAvailability.therapist_id == therapist_id)
            .all()
        )
        max_weekly_sessions = None
        max_weekly_minutes = None
        for b in blocks:
            if b.max_sessions is not None:
                cap = b.max_sessions * 7
                if max_weekly_sessions is None or cap < max_weekly_sessions:
                    max_weekly_sessions = cap
            if b.max_minutes is not None:
                cap = b.max_minutes * 7
                if max_weekly_minutes is None or cap < max_weekly_minutes:
                    max_weekly_minutes = cap

        # If no caps are configured, there's nothing to check
        if max_weekly_sessions is None and max_weekly_minutes is None:
            return []

        weekly_sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date >= week_start,
                SessionModel.date <= week_end,
                SessionModel.id != session.id,
            )
            .all()
        )

        conflicts = []
        if max_weekly_sessions is not None and len(weekly_sessions) >= max_weekly_sessions:
            conflicts.append({
                "type": "WEEKLY_LOAD",
                "detail": (
                    f"Adding this session would exceed inferred weekly max_sessions={max_weekly_sessions} "
                    f"(currently {len(weekly_sessions)})"
                ),
            })

        if max_weekly_minutes is not None:
            weekly_minutes = sum(
                self._duration_minutes(s.start_time, s.end_time, s.date) for s in weekly_sessions
            )
            new_minutes = self._duration_minutes(session.start_time, session.end_time, session.date)
            if weekly_minutes + new_minutes > max_weekly_minutes:
                conflicts.append({
                    "type": "WEEKLY_LOAD",
                    "detail": (
                        f"Adding this session ({new_minutes} min) would exceed inferred weekly "
                        f"max_minutes={max_weekly_minutes} (currently {weekly_minutes} min)"
                    ),
                })

        return conflicts

    def _check_discipline_mismatch(self, therapist, session):
        if therapist is None:
            return []
        if therapist.discipline != session.discipline:
            return [{
                "type": "DISCIPLINE_MISMATCH",
                "detail": (
                    f"Therapist discipline '{therapist.discipline}' does not match "
                    f"session discipline '{session.discipline}'"
                ),
            }]
        return []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def detect_conflicts_for_session(self, session_id: str):
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return None

        if session.therapist_id is None:
            return {
                "session_id": session_id,
                "therapist_id": None,
                "conflicts": [],
                "has_conflicts": False,
            }

        therapist = (
            self.db.query(Therapist)
            .filter(Therapist.therapist_id == session.therapist_id)
            .first()
        )

        conflicts = []
        conflicts += self._check_discipline_mismatch(therapist, session)
        conflicts += self._check_outside_availability(session.therapist_id, session)
        conflicts += self._check_time_off(session.therapist_id, session)
        conflicts += self._check_time_overlap(session.therapist_id, session)
        conflicts += self._check_daily_load(session.therapist_id, session)
        conflicts += self._check_weekly_load(session.therapist_id, session)

        return {
            "session_id": session_id,
            "therapist_id": session.therapist_id,
            "conflicts": conflicts,
            "has_conflicts": len(conflicts) > 0,
        }

    def has_any_conflict(self, therapist_id: str, session) -> bool:
        """Lightweight check used by MatchingService to pre-filter candidates."""
        session_start = datetime.combine(session.date, session.start_time)
        session_end = datetime.combine(session.date, session.end_time)

        # Discipline is handled by MatchingService separately, skip here.
        if self._check_outside_availability(therapist_id, session):
            return True
        if self._check_time_off(therapist_id, session):
            return True

        others = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date == session.date,
                SessionModel.id != session.id,
            )
            .all()
        )
        if any(self._overlaps(s.start_time, s.end_time, session.start_time, session.end_time) for s in others):
            return True

        dow = session.date.weekday()
        blocks = (
            self.db.query(TherapistAvailability)
            .filter(
                TherapistAvailability.therapist_id == therapist_id,
                TherapistAvailability.day_of_week == dow,
            )
            .all()
        )
        covering_block = next(
            (b for b in blocks if b.start_time <= session.start_time and b.end_time >= session.end_time),
            None,
        )
        if covering_block:
            if self._check_daily_load(therapist_id, session):
                return True

        if self._check_weekly_load(therapist_id, session):
            return True

        return False
