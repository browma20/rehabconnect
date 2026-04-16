"""
TherapistPerformanceService
===========================
Aggregates reliability, productivity and caseload-mix signals into a single
composite performance_score for each therapist.

Performance score formula (weights sum to 1.0):
  reliability_score    × 0.40  – cancellations / reschedule rate
  productivity_score   × 0.35  – completion rate + delivered-minutes trend
  caseload_balance     × 0.25  – how evenly workload spreads across disciplines

All individual sub-scores are normalised to 0–100 before weighting.
Change the WEIGHTS constant to re-tune without touching the logic.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session as OrmSession

from app.models.session import Session as SessionModel
from app.models.session_audit_log import SessionAuditLog
from app.models.therapist import Therapist as TherapistModel
from app.services.therapist_analytics_service import TherapistAnalyticsService

# ---------------------------------------------------------------------------
# Tunable constants
# ---------------------------------------------------------------------------
WEIGHTS = {
    "reliability": 0.40,
    "productivity": 0.35,
    "caseload_balance": 0.25,
}

# Minimum sessions required for a meaningful trend (otherwise trend is neutral)
MIN_SESSIONS_FOR_TREND = 4


class TherapistPerformanceService:
    def __init__(self, db: OrmSession):
        self.db = db
        self._analytics = TherapistAnalyticsService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _week_start(self, value: date) -> date:
        return value - timedelta(days=value.weekday())

    def _duration_minutes(self, session: SessionModel) -> int:
        start_dt = datetime.combine(session.date, session.start_time)
        end_dt = datetime.combine(session.date, session.end_time)
        return max(0, int((end_dt - start_dt).total_seconds() / 60))

    def _trend_slope_normalised(self, weekly_minutes: list[float]) -> float:
        """
        Simple linear-regression slope over the weekly delivered-minutes list,
        normalised to 0–100 (50 = flat, >50 = improving, <50 = declining).

        Uses mean-centred OLS: slope = Σ(x - x̄)(y - ȳ) / Σ(x - x̄)².
        """
        n = len(weekly_minutes)
        if n < 2:
            return 50.0

        x_mean = (n - 1) / 2.0
        y_mean = sum(weekly_minutes) / n
        numerator = sum((i - x_mean) * (weekly_minutes[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 50.0

        slope = numerator / denominator  # minutes per week

        # Scale: cap at ±60 min/week change → maps to 0–100 centred on 50
        capped = max(-60.0, min(60.0, slope))
        return round(50.0 + (capped / 60.0) * 50.0, 2)

    def _caseload_balance_score(self, discipline_counts: dict) -> float:
        """
        Measures how evenly sessions are spread across PT/OT/ST.
        Score = 100 × (1 − Gini coefficient).
        Pure single-discipline → Gini = ~0.67 → score ≈ 33.
        Perfectly split → Gini = 0 → score = 100.
        """
        values = sorted(discipline_counts.values())
        n = len(values)
        if n == 0:
            return 100.0

        total = sum(values)
        if total == 0:
            return 100.0

        # Gini: Σ Σ |xi - xj| / (2 * n * total)
        abs_diff_sum = sum(abs(values[i] - values[j]) for i in range(n) for j in range(n))
        gini = abs_diff_sum / (2 * n * total)
        return round((1.0 - gini) * 100.0, 2)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_performance_profile(self, therapist_id: str, weeks: int = 12) -> dict:
        """
        Return a structured performance profile for a single therapist.

        Parameters
        ----------
        therapist_id : str
        weeks        : int  – lookback window (default 12)
        """
        therapist = (
            self.db.query(TherapistModel)
            .filter(TherapistModel.therapist_id == therapist_id)
            .first()
        )
        if not therapist:
            return {"success": False, "error": "Therapist not found"}

        today = date.today()
        lookback_start = self._week_start(today) - timedelta(days=7 * (weeks - 1))
        lookback_end = today

        # ----------------------------------------------------------------
        # (a) Fetch sessions
        # ----------------------------------------------------------------
        sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date >= lookback_start,
                SessionModel.date <= lookback_end,
            )
            .order_by(SessionModel.date)
            .all()
        )
        total_sessions = len(sessions)

        # ----------------------------------------------------------------
        # (b) Reliability metrics from SessionAuditLog
        # ----------------------------------------------------------------
        session_ids = [s.id for s in sessions]
        audits = []
        if session_ids:
            audits = (
                self.db.query(SessionAuditLog)
                .filter(SessionAuditLog.session_id.in_(session_ids))
                .all()
            )

        therapist_cancellations = sum(
            1
            for a in audits
            if a.action_type == "canceled"
            and (a.performed_by or "").startswith("therapist:")
        )
        therapist_reschedules = sum(
            1
            for a in audits
            if a.action_type in {"rescheduled", "smart_rescheduled"}
            and (a.performed_by or "").startswith("therapist:")
        )
        # All reschedules (system + therapist) so we don't undercount instability
        total_reschedules = sum(
            1 for a in audits if a.action_type in {"rescheduled", "smart_rescheduled"}
        )

        cancel_rate = (therapist_cancellations / total_sessions) if total_sessions > 0 else 0.0
        reschedule_rate = (total_reschedules / total_sessions) if total_sessions > 0 else 0.0

        completed_count = sum(1 for s in sessions if s.status == "completed")
        completion_rate = (completed_count / total_sessions) if total_sessions > 0 else 0.0

        # Reliability score: mirrors the formula in TherapistAnalyticsService
        reliability_score = round(
            max(
                0.0,
                min(
                    100.0,
                    (completion_rate * 70.0)
                    + ((1.0 - cancel_rate) * 20.0)
                    + ((1.0 - reschedule_rate) * 10.0),
                ),
            ),
            2,
        )

        # ----------------------------------------------------------------
        # (c) Productivity metrics
        # ----------------------------------------------------------------
        canceled_count = sum(1 for s in sessions if s.status == "canceled")
        rescheduled_count = sum(1 for s in sessions if s.status == "rescheduled")
        delivered_minutes_total = sum(
            self._duration_minutes(s) for s in sessions if s.status == "completed"
        )
        scheduled_minutes_total = sum(self._duration_minutes(s) for s in sessions)

        # Per-week delivered_minutes for trendline
        weekly_delivered: dict[date, float] = {}
        for s in sessions:
            wk = self._week_start(s.date)
            if s.status == "completed":
                weekly_delivered[wk] = weekly_delivered.get(wk, 0.0) + self._duration_minutes(s)

        # Build an ordered list covering all weeks in the window (fill gaps with 0)
        week_starts = sorted(
            {self._week_start(s.date) for s in sessions}
            or {self._week_start(today)}
        )
        delivered_trendline = []
        for wk in week_starts:
            delivered_trendline.append(
                {
                    "week_start": wk.isoformat(),
                    "delivered_minutes": round(weekly_delivered.get(wk, 0.0), 0),
                }
            )

        avg_delivered_per_week = (
            delivered_minutes_total / len(week_starts) if week_starts else 0.0
        )

        # Trend score: OLS slope normalised to 0–100
        if len(delivered_trendline) >= MIN_SESSIONS_FOR_TREND:
            minute_series = [pt["delivered_minutes"] for pt in delivered_trendline]
            trend_score = self._trend_slope_normalised(minute_series)
        else:
            trend_score = 50.0  # neutral for insufficient data

        # Productivity sub-score: blend completion_rate + trend
        productivity_score = round(
            min(100.0, (completion_rate * 70.0) + (trend_score * 0.30)),
            2,
        )

        # ----------------------------------------------------------------
        # (d) Caseload mix
        # ----------------------------------------------------------------
        discipline_counts: dict[str, int] = {}
        for s in sessions:
            disc = (s.discipline or "UNKNOWN").upper()
            discipline_counts[disc] = discipline_counts.get(disc, 0) + 1

        discipline_percentages = {
            disc: round((cnt / total_sessions) * 100, 1) if total_sessions > 0 else 0.0
            for disc, cnt in discipline_counts.items()
        }

        caseload_balance = self._caseload_balance_score(discipline_counts)

        # ----------------------------------------------------------------
        # (e) Composite performance_score
        # ----------------------------------------------------------------
        performance_score = round(
            (reliability_score * WEIGHTS["reliability"])
            + (productivity_score * WEIGHTS["productivity"])
            + (caseload_balance * WEIGHTS["caseload_balance"]),
            2,
        )

        # ----------------------------------------------------------------
        # (f) Structured output
        # ----------------------------------------------------------------
        return {
            "success": True,
            "therapist": {
                "therapist_id": therapist.therapist_id,
                "name": f"{therapist.first_name} {therapist.last_name}",
                "discipline": therapist.discipline,
                "active": therapist.active,
            },
            "range": {
                "start_date": lookback_start.isoformat(),
                "end_date": lookback_end.isoformat(),
                "weeks": weeks,
            },
            "reliability": {
                "total_sessions": total_sessions,
                "completed_sessions": completed_count,
                "canceled_sessions": canceled_count,
                "rescheduled_sessions": rescheduled_count,
                "therapist_cancellations": therapist_cancellations,
                "therapist_reschedules": therapist_reschedules,
                "completion_rate": round(completion_rate, 4),
                "cancel_rate": round(cancel_rate, 4),
                "reschedule_rate": round(reschedule_rate, 4),
                "reliability_score": reliability_score,
            },
            "productivity": {
                "delivered_minutes_total": delivered_minutes_total,
                "scheduled_minutes_total": scheduled_minutes_total,
                "avg_delivered_minutes_per_week": round(avg_delivered_per_week, 1),
                "productivity_trend_score": trend_score,
                "productivity_score": productivity_score,
                "delivered_trendline": delivered_trendline,
            },
            "caseload_mix": {
                "discipline_counts": discipline_counts,
                "discipline_percentages": discipline_percentages,
                "caseload_balance_score": caseload_balance,
            },
            "performance_score": performance_score,
            "scoring_weights": WEIGHTS,
        }

    def get_all_therapists_performance(self, weeks: int = 12) -> dict:
        """
        Return performance profiles for every therapist, sorted by
        performance_score descending.
        """
        therapists = self.db.query(TherapistModel).all()

        profiles = []
        for t in therapists:
            result = self.get_performance_profile(t.therapist_id, weeks=weeks)
            if not result.get("success"):
                continue
            profiles.append(result)

        profiles.sort(key=lambda p: p["performance_score"], reverse=True)

        today = date.today()
        lookback_start = (
            self._week_start(today) - timedelta(days=7 * (weeks - 1))
        ).isoformat()

        return {
            "success": True,
            "range": {
                "start_date": lookback_start,
                "end_date": today.isoformat(),
                "weeks": weeks,
            },
            "count": len(profiles),
            "scoring_weights": WEIGHTS,
            "therapists": profiles,
        }
