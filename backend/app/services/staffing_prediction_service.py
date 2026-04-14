from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session as OrmSession
from backend.app.models.session import Session as SessionModel
from backend.app.models.therapist import Therapist
from backend.app.models.therapist_availability import TherapistAvailability, TherapistTimeOff

# gap/supply ratios that define risk bands
_RISK_HIGH_THRESHOLD = 0.10    # less than 10 % buffer → HIGH
_RISK_MEDIUM_THRESHOLD = 0.25  # less than 25 % buffer → MEDIUM


class StaffingPredictionService:
    def __init__(self, db: OrmSession):
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _block_minutes(self, avail: TherapistAvailability) -> int:
        """Available minutes in one TherapistAvailability block, honouring max_minutes."""
        ref = date.today()
        start_dt = datetime.combine(ref, avail.start_time)
        end_dt = datetime.combine(ref, avail.end_time)
        raw = int((end_dt - start_dt).total_seconds() / 60)
        if avail.max_minutes:
            return min(raw, avail.max_minutes)
        return raw

    def _session_minutes(self, session: SessionModel) -> int:
        """duration_minutes for a scheduled session."""
        ref = session.date
        start_dt = datetime.combine(ref, session.start_time)
        end_dt = datetime.combine(ref, session.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)

    def _therapist_on_time_off(self, therapist_id: str, day: date) -> bool:
        """True if any TherapistTimeOff block overlaps the given calendar day."""
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day + timedelta(days=1), datetime.min.time())
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

    def _risk_level(self, supply: int, gap: int) -> str:
        """Assign HIGH / MEDIUM / LOW based on the buffer ratio."""
        if supply == 0:
            return "HIGH" if gap < 0 else "LOW"
        ratio = gap / supply
        if ratio < _RISK_HIGH_THRESHOLD:
            return "HIGH"
        if ratio < _RISK_MEDIUM_THRESHOLD:
            return "MEDIUM"
        return "LOW"

    def _recommendation(self, discipline: str, risk: str, gap: int) -> str:
        if risk == "HIGH":
            return (
                f"Critical staffing shortage in {discipline}. "
                f"Deficit of {abs(gap)} minutes. Consider immediate hire or contract staff."
            )
        if risk == "MEDIUM":
            return (
                f"Moderate staffing pressure in {discipline}. "
                f"Only {gap} minutes of buffer. Monitor closely and consider PRN coverage."
            )
        return f"{discipline} staffing is adequate with {gap} minutes of buffer."

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict_staffing(self, week_start: date, days: int = 7) -> dict:
        """
        Returns a structured staffing prediction for the requested window.

        Parameters
        ----------
        week_start : date
            First day of the window (inclusive).
        days : int
            Number of calendar days to analyse (default 7).
        """
        week_end = week_start + timedelta(days=days)
        week_days = [week_start + timedelta(days=i) for i in range(days)]

        # ---- Demand: all scheduled sessions in the window -----------
        sessions = (
            self.db.query(SessionModel)
            .filter(SessionModel.date >= week_start, SessionModel.date < week_end)
            .all()
        )

        # demand_by_disc[discipline][day_iso] = total minutes
        demand_by_disc: dict[str, dict[str, int]] = {}
        for s in sessions:
            d_iso = s.date.isoformat()
            disc = s.discipline
            demand_by_disc.setdefault(disc, {})
            demand_by_disc[disc][d_iso] = demand_by_disc[disc].get(d_iso, 0) + self._session_minutes(s)

        # ---- Supply: net available minutes per therapist per day ----
        therapists = (
            self.db.query(Therapist).filter(Therapist.active == True).all()
        )

        # supply_by_disc[discipline][day_iso] = total available minutes
        supply_by_disc: dict[str, dict[str, int]] = {}
        for therapist in therapists:
            disc = therapist.discipline
            supply_by_disc.setdefault(disc, {})

            for day in week_days:
                d_iso = day.isoformat()
                supply_by_disc[disc].setdefault(d_iso, 0)

                # Therapist is fully unavailable on this day
                if self._therapist_on_time_off(therapist.therapist_id, day):
                    continue

                # Gross available minutes from availability blocks
                avail_blocks = (
                    self.db.query(TherapistAvailability)
                    .filter(
                        TherapistAvailability.therapist_id == therapist.therapist_id,
                        TherapistAvailability.day_of_week == day.weekday(),
                    )
                    .all()
                )
                available_minutes = sum(self._block_minutes(b) for b in avail_blocks)

                # Subtract already-committed session minutes on this day
                committed_minutes = sum(
                    self._session_minutes(s)
                    for s in sessions
                    if s.therapist_id == therapist.therapist_id and s.date == day
                )

                net = max(0, available_minutes - committed_minutes)
                supply_by_disc[disc][d_iso] += net

        # ---- Compile breakdowns -------------------------------------
        all_disciplines = sorted(set(demand_by_disc.keys()) | set(supply_by_disc.keys()))

        # Daily breakdown
        daily_breakdown: dict = {}
        for day in week_days:
            d_iso = day.isoformat()
            day_demand = 0
            day_supply = 0
            by_disc: dict = {}

            for disc in all_disciplines:
                d_min = demand_by_disc.get(disc, {}).get(d_iso, 0)
                s_min = supply_by_disc.get(disc, {}).get(d_iso, 0)
                gap = s_min - d_min
                day_demand += d_min
                day_supply += s_min
                by_disc[disc] = {
                    "demand_minutes": d_min,
                    "supply_minutes": s_min,
                    "gap_minutes": gap,
                    "risk": self._risk_level(s_min, gap),
                }

            day_gap = day_supply - day_demand
            daily_breakdown[d_iso] = {
                "demand_minutes": day_demand,
                "supply_minutes": day_supply,
                "gap_minutes": day_gap,
                "risk": self._risk_level(day_supply, day_gap),
                "by_discipline": by_disc,
            }

        # Discipline breakdown (aggregate over the whole window)
        discipline_breakdown: dict = {}
        for disc in all_disciplines:
            total_demand = sum(
                demand_by_disc.get(disc, {}).get(d.isoformat(), 0) for d in week_days
            )
            total_supply = sum(
                supply_by_disc.get(disc, {}).get(d.isoformat(), 0) for d in week_days
            )
            gap = total_supply - total_demand
            risk = self._risk_level(total_supply, gap)
            discipline_breakdown[disc] = {
                "demand_minutes": total_demand,
                "supply_minutes": total_supply,
                "gap_minutes": gap,
                "risk": risk,
                "recommendation": self._recommendation(disc, risk, gap),
            }

        # Overall risk = worst single-discipline risk
        risk_rank = {"HIGH": 2, "MEDIUM": 1, "LOW": 0}
        overall_risk = max(
            (d["risk"] for d in discipline_breakdown.values()),
            key=lambda r: risk_rank[r],
            default="LOW",
        )

        return {
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "days": days,
            "overall_risk": overall_risk,
            "disciplines": discipline_breakdown,
            "daily": daily_breakdown,
        }
