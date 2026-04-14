"""
HiringRecommendationService
===========================
Synthesizes capacity, performance, and reliability signals to generate
actionable hiring recommendations per discipline.

Pipeline:
  1. Get capacity forecast (demand/supply/gap) from CapacityPlanningService
  2. Get therapist performance profiles from TherapistPerformanceService
  3. Query for unassigned sessions (proxy for marketplace failures)
  4. Get unresolved predictive alerts (shortage/overload indicators)
  5. For each discipline:
     - Convert gap_minutes to base FTE
     - Adjust FTE based on average team reliability (if <80%, increase needed)
     - Adjust FTE based on marketplace failures (unassigned sessions count)
     - Surface critical alerts (shortage/overloaded/unassigned-at-risk)
     - Build human-readable recommendation

All metrics feed into a confidence/urgency assessment.
"""

from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy import and_

from backend.app.models.session import Session as SessionModel
from backend.app.models.therapist import Therapist as TherapistModel
from backend.app.services.capacity_planning_service import CapacityPlanningService
from backend.app.services.therapist_performance_service import TherapistPerformanceService
from backend.app.services.predictive_alert_service import PredictiveAlertService

# ---------------------------------------------------------------------------
# Tunable constants
# ---------------------------------------------------------------------------
MINUTES_PER_WEEK_FULL_TIME = 2400  # 40 hours/week
RELIABILITY_THRESHOLD = 80.0  # If avg reliability < 80%, increase hiring need
MARKETPLACE_FAILURE_WEIGHT = 0.5  # Unassigned session → 0.5 FTE adjustment

# Discipline rankings (for priority sorting in output)
DISCIPLINE_PRIORITY = {"PT": 0, "OT": 1, "ST": 2}


class HiringRecommendationService:
    def __init__(self, db: OrmSession):
        self.db = db
        self._capacity = CapacityPlanningService(db)
        self._performance = TherapistPerformanceService(db)
        self._alerts = PredictiveAlertService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _week_monday(self, value: date) -> date:
        return value - timedelta(days=value.weekday())

    def _unassigned_session_count(self, discipline: str, weeks: int) -> int:
        """Count unassigned sessions in the forecast window for a discipline."""
        today = date.today()
        window_start = self._week_monday(today)
        window_end = window_start + timedelta(days=7 * weeks)

        return (
            self.db.query(SessionModel)
            .filter(
                SessionModel.discipline == discipline.upper(),
                SessionModel.therapist_id == None,
                SessionModel.status != "canceled",
                SessionModel.date >= window_start,
                SessionModel.date <= window_end,
            )
            .count()
        )

    def _active_therapist_count(self, discipline: str) -> int:
        """Current count of active therapists in the discipline."""
        return (
            self.db.query(TherapistModel)
            .filter(
                TherapistModel.active == True,
                TherapistModel.discipline == discipline.upper(),
            )
            .count()
        )

    def _get_discipline_alerts(self, discipline: str) -> dict:
        """
        Query unresolved predictive alerts for this discipline.
        Returns counts keyed by alert type.
        """
        today = date.today()
        alerts_result = self._alerts.list_alerts(
            resolved=False,
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=7),
        )

        if not alerts_result.get("success"):
            return {}

        alerts = alerts_result.get("alerts", [])
        counts = {
            "shortage": 0,
            "overload": 0,
            "unassigned_at_risk": 0,
            "time_off_impact": 0,
        }

        for alert in alerts:
            alert_type = alert.get("type", "").lower()
            msg = alert.get("message", "").lower()
            if discipline.lower() in msg:
                if "shortage" in alert_type:
                    counts["shortage"] += 1
                elif "overload" in alert_type:
                    counts["overload"] += 1
                elif "unassigned" in alert_type:
                    counts["unassigned_at_risk"] += 1
                elif "time_off" in alert_type:
                    counts["time_off_impact"] += 1

        return counts

    def _minutes_to_fte(self, minutes: int) -> float:
        """Convert minutes to FTE (full-time equivalent)."""
        return round(max(0.0, minutes / MINUTES_PER_WEEK_FULL_TIME), 2)

    def _get_recommendation_text(
        self,
        discipline: str,
        base_fte: float,
        reliability_adjustment_fte: float,
        failure_adjustment_fte: float,
        total_fte: float,
        alerts: dict,
        current_headcount: int,
    ) -> str:
        """Build a human-readable recommendation string."""
        lines = []

        if total_fte <= 0.25:
            level = "Low Priority"
            action = "Monitor capacity trends"
        elif total_fte <= 0.75:
            level = "Medium Priority"
            action = "Plan hiring within 6–12 weeks"
        elif total_fte <= 1.5:
            level = "High Priority"
            action = "Initiate hiring process within 4 weeks"
        else:
            level = "Critical Priority"
            action = "Urgent hiring required within 2 weeks"

        lines.append(f"{level}: Recommend adding {total_fte} FTE")
        lines.append(action)

        if base_fte > 0:
            lines.append(
                f"\n  Base demand (capacity gap): {base_fte} FTE "
                f"({base_fte * MINUTES_PER_WEEK_FULL_TIME:.0f} min/week)"
            )

        if reliability_adjustment_fte != 0:
            sign = "+" if reliability_adjustment_fte > 0 else ""
            lines.append(
                f"  Reliability adjustment: {sign}{reliability_adjustment_fte} FTE "
                f"(current avg reliability below {RELIABILITY_THRESHOLD}%)"
            )

        if failure_adjustment_fte > 0:
            lines.append(
                f"  Marketplace adjustment: +{failure_adjustment_fte} FTE "
                f"({self._unassigned_session_count(discipline, 12)} unassigned sessions)"
            )

        lines.append(f"\n  Current headcount: {current_headcount} therapists")

        if alerts.get("shortage", 0) > 0:
            lines.append(f"  ⚠️ {alerts['shortage']} shortage alert(s) in last 30 days")
        if alerts.get("overload", 0) > 0:
            lines.append(f"  ⚠️ {alerts['overload']} overload alert(s) in last 30 days")
        if alerts.get("unassigned_at_risk", 0) > 0:
            lines.append(
                f"  ⚠️ {alerts['unassigned_at_risk']} unassigned-at-risk alert(s)"
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def generate_recommendation_for_discipline(
        self, discipline: str, weeks: int = 12
    ) -> dict:
        """
        Generate a hiring recommendation for a single discipline.
        """
        discipline = discipline.upper()

        # Get capacity forecast
        forecast = self._capacity.forecast_discipline(discipline, weeks)
        if not forecast.get("success"):
            return {
                "success": False,
                "error": f"Could not forecast capacity for {discipline}",
            }

        # Extract gap from the latest week in the forecast
        forecast_items = forecast.get("forecast", [])
        if not forecast_items:
            latest_gap = 0
        else:
            latest_gap = forecast_items[-1].get("gap_minutes", 0)

        # Get therapist performance profiles for this discipline
        perf_result = self._performance.get_all_therapists_performance(weeks=weeks)
        discipline_profiles = [
            p
            for p in perf_result.get("therapists", [])
            if p.get("therapist", {}).get("discipline") == discipline
        ]

        # Calculate average reliability for the discipline
        if discipline_profiles:
            avg_reliability = sum(
                p.get("reliability", {}).get("reliability_score", 50)
                for p in discipline_profiles
            ) / len(discipline_profiles)
        else:
            avg_reliability = 50.0

        # Count current active therapists
        current_headcount = self._active_therapist_count(discipline)

        # Count unassigned sessions (marketplace failure indicator)
        unassigned_count = self._unassigned_session_count(discipline, weeks)

        # Get predictive alerts
        alerts = self._get_discipline_alerts(discipline)

        # ----------------------------------------------------------------
        # Calculate FTE adjustments
        # ----------------------------------------------------------------
        base_fte = self._minutes_to_fte(max(0, latest_gap))

        # Reliability adjustment: if average reliability < threshold, boost hiring
        if avg_reliability < RELIABILITY_THRESHOLD:
            reliability_factor = (RELIABILITY_THRESHOLD - avg_reliability) / 100.0
            reliability_adjustment_fte = round(base_fte * reliability_factor, 2)
        else:
            reliability_adjustment_fte = 0.0

        # Marketplace adjustment: unassigned sessions indicate matching friction
        failure_adjustment_fte = round(
            unassigned_count * MARKETPLACE_FAILURE_WEIGHT / MINUTES_PER_WEEK_FULL_TIME,
            2,
        )

        total_fte = base_fte + reliability_adjustment_fte + failure_adjustment_fte

        # Build recommendation text
        recommendation_text = self._get_recommendation_text(
            discipline,
            base_fte,
            reliability_adjustment_fte,
            failure_adjustment_fte,
            total_fte,
            alerts,
            current_headcount,
        )

        return {
            "success": True,
            "discipline": discipline,
            "weeks": weeks,
            "generated_at": date.today().isoformat(),
            "hiring_recommendation": {
                "total_fte_needed": total_fte,
                "base_fte": base_fte,
                "reliability_adjustment_fte": reliability_adjustment_fte,
                "marketplace_adjustment_fte": failure_adjustment_fte,
                "current_headcount": current_headcount,
                "recommended_total_headcount": current_headcount + int(total_fte + 0.5),
            },
            "supporting_data": {
                "avg_reliability_score": round(avg_reliability, 1),
                "unassigned_sessions_count": unassigned_count,
                "latest_gap_minutes": latest_gap,
                "unresolved_alerts": alerts,
                "therapist_profiles_count": len(discipline_profiles),
            },
            "recommendation_text": recommendation_text,
        }

    def generate_recommendations(self, weeks: int = 12) -> dict:
        """
        Generate hiring recommendations for all disciplines.
        Returns sorted by priority (highest FTE need first).
        """
        recommendations = []

        for discipline in ["PT", "OT", "ST"]:
            result = self.generate_recommendation_for_discipline(
                discipline, weeks=weeks
            )
            if result.get("success"):
                recommendations.append(result)

        # Sort by total_fte_needed descending (highest need first)
        recommendations.sort(
            key=lambda r: r["hiring_recommendation"]["total_fte_needed"],
            reverse=True,
        )

        total_fte_across_disciplines = sum(
            r["hiring_recommendation"]["total_fte_needed"] for r in recommendations
        )

        return {
            "success": True,
            "generated_at": date.today().isoformat(),
            "weeks": weeks,
            "summary": {
                "total_fte_needed_all_disciplines": round(total_fte_across_disciplines, 2),
                "discipline_count": len(recommendations),
                "reliability_threshold": RELIABILITY_THRESHOLD,
                "minutes_per_week_full_time": MINUTES_PER_WEEK_FULL_TIME,
            },
            "recommendations": recommendations,
        }
