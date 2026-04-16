from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session as OrmSession

from app.models.session import Session as SessionModel
from app.models.session_audit_log import SessionAuditLog
from app.models.therapist import Therapist as TherapistModel
from app.models.therapist_availability import TherapistAvailability, TherapistTimeOff
from app.services.therapist_analytics_service import TherapistAnalyticsService

LOOKBACK_WEEKS = 8
DEFAULT_DISCIPLINES = ["OT", "PT", "ST"]


class CapacityPlanningService:
    def __init__(self, db: OrmSession):
        self.db = db
        self._analytics = TherapistAnalyticsService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _week_monday(self, value: date) -> date:
        return value - timedelta(days=value.weekday())

    def _duration_minutes(self, session: SessionModel) -> int:
        start_dt = datetime.combine(session.date, session.start_time)
        end_dt = datetime.combine(session.date, session.end_time)
        return max(0, int((end_dt - start_dt).total_seconds() / 60))

    def _block_minutes(self, block: TherapistAvailability) -> int:
        ref = date.today()
        raw = max(
            0,
            int(
                (
                    datetime.combine(ref, block.end_time)
                    - datetime.combine(ref, block.start_time)
                ).total_seconds()
                / 60
            ),
        )
        return min(raw, block.max_minutes) if block.max_minutes else raw

    def _therapist_on_time_off(self, therapist_id: str, day: date) -> bool:
        day_start = datetime.combine(day, time.min)
        day_end = datetime.combine(day + timedelta(days=1), time.min)
        return (
            self.db.query(TherapistTimeOff)
            .filter(
                TherapistTimeOff.therapist_id == therapist_id,
                TherapistTimeOff.start_datetime < day_end,
                TherapistTimeOff.end_datetime > day_start,
            )
            .first()
            is not None
        )

    def _therapist_time_off_days(
        self, therapist_id: str, week_start: date, week_end: date
    ) -> list:
        return [
            (week_start + timedelta(days=i)).isoformat()
            for i in range(7)
            if self._therapist_on_time_off(therapist_id, week_start + timedelta(days=i))
        ]

    def _raw_weekly_supply(self, therapist_id: str, week_start: date) -> int:
        total = 0
        for i in range(7):
            day = week_start + timedelta(days=i)
            if self._therapist_on_time_off(therapist_id, day):
                continue
            blocks = (
                self.db.query(TherapistAvailability)
                .filter(
                    TherapistAvailability.therapist_id == therapist_id,
                    TherapistAvailability.day_of_week == day.weekday(),
                )
                .all()
            )
            total += sum(self._block_minutes(b) for b in blocks)
        return total

    def _historical_stats(self, discipline: str, today: date) -> dict:
        """
        Compute trailing LOOKBACK_WEEKS weeks of demand and cancellation/reschedule
        rates for the given discipline.
        """
        week0 = self._week_monday(today)
        lookback_start = week0 - timedelta(days=7 * LOOKBACK_WEEKS)
        lookback_end = week0 - timedelta(days=1)

        sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.discipline == discipline,
                SessionModel.date >= lookback_start,
                SessionModel.date <= lookback_end,
            )
            .all()
        )

        if not sessions:
            return {
                "lookback_weeks": LOOKBACK_WEEKS,
                "avg_weekly_demand_minutes": 0,
                "cancellation_rate": 0.0,
                "reschedule_rate": 0.0,
            }

        total = len(sessions)
        canceled = sum(1 for s in sessions if s.status == "canceled")
        rescheduled = sum(1 for s in sessions if s.status == "rescheduled")

        session_ids = [s.id for s in sessions]
        audit_reschedules = (
            self.db.query(SessionAuditLog)
            .filter(
                SessionAuditLog.session_id.in_(session_ids),
                SessionAuditLog.action_type.in_(["rescheduled", "smart_rescheduled"]),
            )
            .count()
        )

        demand_minutes = sum(
            self._duration_minutes(s)
            for s in sessions
            if s.status != "canceled"
        )
        avg_weekly = round(demand_minutes / LOOKBACK_WEEKS)
        cancel_rate = round(canceled / total, 4)
        reschedule_rate = round(max(rescheduled, audit_reschedules) / total, 4)

        return {
            "lookback_weeks": LOOKBACK_WEEKS,
            "avg_weekly_demand_minutes": avg_weekly,
            "cancellation_rate": cancel_rate,
            "reschedule_rate": reschedule_rate,
        }

    def _discipline_productivity(
        self, discipline: str, today: date
    ) -> tuple[float, float]:
        """
        Return (avg_utilization_rate, avg_reliability_rate) for all active therapists
        of the given discipline using the last LOOKBACK_WEEKS weeks of data.
        """
        week0 = self._week_monday(today)
        lookback_start = week0 - timedelta(days=7 * LOOKBACK_WEEKS)
        lookback_end = week0 - timedelta(days=1)

        therapists = (
            self.db.query(TherapistModel)
            .filter(
                TherapistModel.active == True,
                TherapistModel.discipline == discipline,
            )
            .all()
        )

        util_scores = []
        reliability_scores = []
        for therapist in therapists:
            result = self._analytics.get_productivity(
                therapist.therapist_id, lookback_start, lookback_end
            )
            if result.get("success"):
                util_scores.append(result["metrics"]["utilization_rate"])
                reliability_scores.append(
                    result["audit_insights"]["reliability_score"] / 100.0
                )

        avg_util = round(sum(util_scores) / len(util_scores), 4) if util_scores else 1.0
        avg_rel = (
            round(sum(reliability_scores) / len(reliability_scores), 4)
            if reliability_scores
            else 1.0
        )
        return avg_util, avg_rel

    def _risk_score(self, effective_demand: int, effective_supply: int) -> int:
        """
        0 = comfortable excess capacity, 100 = critical shortage.

        When supply >= demand:
          risk = 0–30 proportional to how thin the buffer is.
        When supply < demand:
          risk = 30–100 proportional to the shortfall ratio.
        """
        if effective_demand <= 0:
            return 0
        if effective_supply >= effective_demand:
            buffer_ratio = (effective_supply - effective_demand) / effective_demand
            return max(0, round((1.0 - min(buffer_ratio, 1.0)) * 30))
        shortage_ratio = (effective_demand - effective_supply) / effective_demand
        return min(100, 30 + round(shortage_ratio * 70))

    def _recommendation(self, risk_score: int, discipline: str, gap_minutes: int) -> str:
        sign = f"{gap_minutes:+}"
        if risk_score <= 20:
            return (
                f"{discipline} capacity is adequate — buffer of "
                f"{abs(gap_minutes)} min ({sign} min gap)."
            )
        if risk_score <= 40:
            return (
                f"{discipline} capacity is healthy but narrowing "
                f"({sign} min gap). Monitor and consider PRN coverage."
            )
        if risk_score <= 60:
            return (
                f"Moderate {discipline} capacity pressure ({sign} min gap). "
                f"Plan PRN or recruit part-time staff."
            )
        if risk_score <= 80:
            return (
                f"High {discipline} staffing gap ({sign} min). "
                f"Active recruitment is recommended."
            )
        return (
            f"CRITICAL {discipline} shortage ({sign} min gap). "
            f"Immediate staffing action required."
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def forecast_discipline(self, discipline: str, weeks: int = 12) -> dict:
        """Week-by-week capacity forecast for a single discipline."""
        today = date.today()
        week0 = self._week_monday(today)
        historical = self._historical_stats(discipline, today)
        avg_util, avg_rel = self._discipline_productivity(discipline, today)

        therapists = (
            self.db.query(TherapistModel)
            .filter(
                TherapistModel.active == True,
                TherapistModel.discipline == discipline,
            )
            .all()
        )

        forecast_weeks = []
        for i in range(weeks):
            week_start = week0 + timedelta(days=7 * i)
            week_end = week_start + timedelta(days=6)

            # ---- Demand ----
            scheduled = (
                self.db.query(SessionModel)
                .filter(
                    SessionModel.discipline == discipline,
                    SessionModel.date >= week_start,
                    SessionModel.date <= week_end,
                    SessionModel.status != "canceled",
                )
                .all()
            )
            raw_demand = (
                sum(self._duration_minutes(s) for s in scheduled)
                if scheduled
                else historical["avg_weekly_demand_minutes"]
            )
            effective_demand = round(
                raw_demand * (1.0 - historical["cancellation_rate"])
            )

            # ---- Supply ----
            raw_supply = sum(
                self._raw_weekly_supply(t.therapist_id, week_start)
                for t in therapists
            )
            effective_supply = round(raw_supply * avg_util * avg_rel)

            gap = effective_supply - effective_demand
            risk = self._risk_score(effective_demand, effective_supply)

            forecast_weeks.append(
                {
                    "week_number": i + 1,
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "demand_minutes": raw_demand,
                    "effective_demand_minutes": effective_demand,
                    "supply_minutes": raw_supply,
                    "effective_supply_minutes": effective_supply,
                    "gap_minutes": gap,
                    "risk_score": risk,
                    "recommendation": self._recommendation(risk, discipline, gap),
                }
            )

        return {
            "discipline": discipline,
            "weeks": weeks,
            "generated_at": datetime.utcnow().isoformat(),
            "historical": historical,
            "adjustments": {
                "avg_utilization_rate": avg_util,
                "avg_reliability_rate": avg_rel,
                "effective_supply_factor": round(avg_util * avg_rel, 4),
            },
            "forecast": forecast_weeks,
        }

    def forecast_all_disciplines(self, weeks: int = 12) -> dict:
        """Forecast for every active discipline; returns a combined dashboard."""
        discipline_rows = (
            self.db.query(TherapistModel.discipline)
            .filter(TherapistModel.active == True)
            .distinct()
            .all()
        )
        disciplines = sorted(
            set(row[0] for row in discipline_rows) or DEFAULT_DISCIPLINES
        )

        results = {d: self.forecast_discipline(d, weeks) for d in disciplines}

        # Summary: highest single-week risk across all disciplines
        highest_risk_discipline = None
        overall_risk_score = 0
        if results:
            for disc, data in results.items():
                disc_max_risk = max(
                    (w["risk_score"] for w in data["forecast"]), default=0
                )
                if disc_max_risk > overall_risk_score:
                    overall_risk_score = disc_max_risk
                    highest_risk_discipline = disc

        return {
            "weeks": weeks,
            "generated_at": datetime.utcnow().isoformat(),
            "disciplines": results,
            "summary": {
                "disciplines_analyzed": len(results),
                "highest_risk_discipline": highest_risk_discipline,
                "overall_risk_score": overall_risk_score,
            },
        }

    def forecast_therapist(self, therapist_id: str, weeks: int = 12) -> dict:
        """Week-by-week supply and workload forecast for a single therapist."""
        therapist = (
            self.db.query(TherapistModel)
            .filter(TherapistModel.therapist_id == therapist_id)
            .first()
        )
        if not therapist:
            return {"success": False, "error": "Therapist not found"}

        today = date.today()
        week0 = self._week_monday(today)
        lookback_start = week0 - timedelta(days=7 * LOOKBACK_WEEKS)
        lookback_end = week0 - timedelta(days=1)

        analytics = self._analytics.get_productivity(
            therapist_id, lookback_start, lookback_end
        )
        if analytics.get("success"):
            utilization_rate = analytics["metrics"]["utilization_rate"]
            reliability_score = analytics["audit_insights"]["reliability_score"]
        else:
            utilization_rate = 1.0
            reliability_score = 100.0

        reliability_rate = reliability_score / 100.0
        effective_factor = round(utilization_rate * reliability_rate, 4)

        forecast_weeks = []
        for i in range(weeks):
            week_start = week0 + timedelta(days=7 * i)
            week_end = week_start + timedelta(days=6)

            raw_supply = self._raw_weekly_supply(therapist_id, week_start)
            effective_supply = round(raw_supply * effective_factor)

            committed_sessions = (
                self.db.query(SessionModel)
                .filter(
                    SessionModel.therapist_id == therapist_id,
                    SessionModel.date >= week_start,
                    SessionModel.date <= week_end,
                    SessionModel.status != "canceled",
                )
                .all()
            )
            committed_minutes = sum(
                self._duration_minutes(s) for s in committed_sessions
            )
            available_minutes = max(0, effective_supply - committed_minutes)
            time_off_days = self._therapist_time_off_days(
                therapist_id, week_start, week_end
            )

            forecast_weeks.append(
                {
                    "week_number": i + 1,
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "raw_supply_minutes": raw_supply,
                    "effective_supply_minutes": effective_supply,
                    "committed_minutes": committed_minutes,
                    "committed_sessions": len(committed_sessions),
                    "available_minutes": available_minutes,
                    "time_off_days": time_off_days,
                }
            )

        return {
            "success": True,
            "therapist_id": therapist_id,
            "name": f"{therapist.first_name} {therapist.last_name}",
            "discipline": therapist.discipline,
            "active": therapist.active,
            "weeks": weeks,
            "generated_at": datetime.utcnow().isoformat(),
            "historical": {
                "lookback_weeks": LOOKBACK_WEEKS,
                "utilization_rate": round(utilization_rate, 4),
                "reliability_score": round(reliability_score, 2),
                "reliability_rate": round(reliability_rate, 4),
                "effective_factor": effective_factor,
            },
            "forecast": forecast_weeks,
        }
