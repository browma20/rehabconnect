from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session as OrmSession

from app.models.session import Session as SessionModel
from app.models.session_audit_log import SessionAuditLog
from app.models.therapist import Therapist as TherapistModel


class TherapistAnalyticsService:
    def __init__(self, db: OrmSession):
        self.db = db

    def _duration_minutes(self, session: SessionModel) -> int:
        start_dt = datetime.combine(session.date, session.start_time)
        end_dt = datetime.combine(session.date, session.end_time)
        minutes = int((end_dt - start_dt).total_seconds() / 60)
        return max(minutes, 0)

    def _week_start(self, value: date) -> date:
        return value - timedelta(days=value.weekday())

    def _build_trendline(self, therapist_id: str, end_date: date, weeks: int = 8) -> list:
        week_points = []
        current_week_start = self._week_start(end_date)

        for i in range(weeks - 1, -1, -1):
            week_start = current_week_start - timedelta(days=7 * i)
            week_end = week_start + timedelta(days=6)

            sessions = (
                self.db.query(SessionModel)
                .filter(
                    SessionModel.therapist_id == therapist_id,
                    SessionModel.date >= week_start,
                    SessionModel.date <= week_end,
                )
                .all()
            )

            completed_sessions = [s for s in sessions if s.status == "completed"]
            delivered_minutes = sum(self._duration_minutes(s) for s in completed_sessions)
            scheduled_minutes = sum(self._duration_minutes(s) for s in sessions)
            utilization_rate = (delivered_minutes / scheduled_minutes) if scheduled_minutes > 0 else 0.0

            week_points.append(
                {
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat(),
                    "completed_sessions": len(completed_sessions),
                    "scheduled_sessions": len(sessions),
                    "delivered_minutes": delivered_minutes,
                    "scheduled_minutes": scheduled_minutes,
                    "utilization_rate": round(utilization_rate, 4),
                }
            )

        return week_points

    def get_productivity(self, therapist_id: str, start_date: date, end_date: date) -> dict:
        therapist = (
            self.db.query(TherapistModel)
            .filter(TherapistModel.therapist_id == therapist_id)
            .first()
        )
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
            .all()
        )

        session_ids = [s.id for s in sessions]
        audits = []
        if session_ids:
            audits = (
                self.db.query(SessionAuditLog)
                .filter(SessionAuditLog.session_id.in_(session_ids))
                .all()
            )

        completed_sessions = sum(1 for s in sessions if s.status == "completed")
        canceled_total = sum(1 for s in sessions if s.status == "canceled")
        rescheduled_sessions = sum(1 for s in sessions if s.status == "rescheduled")

        delivered_minutes = sum(self._duration_minutes(s) for s in sessions if s.status == "completed")
        scheduled_minutes = sum(self._duration_minutes(s) for s in sessions)
        utilization_rate = (delivered_minutes / scheduled_minutes) if scheduled_minutes > 0 else 0.0

        audit_reschedules = sum(1 for a in audits if a.action_type in {"rescheduled", "smart_rescheduled"})
        therapist_initiated_cancellations = sum(
            1
            for a in audits
            if a.action_type == "canceled" and (a.performed_by or "").startswith("therapist:")
        )
        family_initiated_cancellations = sum(
            1
            for a in audits
            if a.action_type == "canceled" and (a.performed_by or "").startswith("family:")
        )

        # Fallback heuristic when performed_by attribution is unavailable.
        if canceled_total > (therapist_initiated_cancellations + family_initiated_cancellations):
            unresolved = canceled_total - therapist_initiated_cancellations - family_initiated_cancellations
            for s in sessions:
                if unresolved <= 0:
                    break
                if s.status != "canceled":
                    continue
                reason = (s.cancellation_reason or "").lower()
                if any(k in reason for k in ["family", "patient", "guardian", "caregiver"]):
                    family_initiated_cancellations += 1
                    unresolved -= 1

        total_sessions = len(sessions)
        completion_rate = (completed_sessions / total_sessions) if total_sessions > 0 else 0.0
        therapist_cancel_rate = (therapist_initiated_cancellations / total_sessions) if total_sessions > 0 else 0.0
        reschedule_rate = (audit_reschedules / total_sessions) if total_sessions > 0 else 0.0

        reliability_score = round(
            max(
                0.0,
                min(
                    100.0,
                    (completion_rate * 70.0) + ((1.0 - therapist_cancel_rate) * 20.0) + ((1.0 - reschedule_rate) * 10.0),
                ),
            ),
            2,
        )

        trendline = self._build_trendline(therapist_id, end_date=end_date, weeks=8)

        return {
            "success": True,
            "therapist": {
                "therapist_id": therapist.therapist_id,
                "name": f"{therapist.first_name} {therapist.last_name}",
                "discipline": therapist.discipline,
                "active": therapist.active,
            },
            "range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "metrics": {
                "completed_sessions": completed_sessions,
                "canceled_sessions": {
                    "total": canceled_total,
                    "therapist": therapist_initiated_cancellations,
                    "family": family_initiated_cancellations,
                },
                "rescheduled_sessions": rescheduled_sessions,
                "delivered_minutes": delivered_minutes,
                "scheduled_minutes": scheduled_minutes,
                "utilization_rate": round(utilization_rate, 4),
            },
            "audit_insights": {
                "reschedules": audit_reschedules,
                "therapist_initiated_cancellations": therapist_initiated_cancellations,
                "reliability_score": reliability_score,
            },
            "trendline": trendline,
        }

    def get_all_therapists_productivity(self, start_date: date, end_date: date) -> dict:
        therapists = self.db.query(TherapistModel).all()
        items = []

        for therapist in therapists:
            result = self.get_productivity(therapist.therapist_id, start_date, end_date)
            if not result.get("success"):
                continue

            items.append(
                {
                    "therapist_id": therapist.therapist_id,
                    "name": result["therapist"]["name"],
                    "discipline": result["therapist"]["discipline"],
                    "active": result["therapist"]["active"],
                    "completed_sessions": result["metrics"]["completed_sessions"],
                    "canceled_sessions_total": result["metrics"]["canceled_sessions"]["total"],
                    "delivered_minutes": result["metrics"]["delivered_minutes"],
                    "scheduled_minutes": result["metrics"]["scheduled_minutes"],
                    "utilization_rate": result["metrics"]["utilization_rate"],
                    "reliability_score": result["audit_insights"]["reliability_score"],
                }
            )

        items.sort(key=lambda x: (-x["reliability_score"], -x["utilization_rate"], x["name"]))

        return {
            "success": True,
            "range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "count": len(items),
            "therapists": items,
        }
