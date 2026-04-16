from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

from sqlalchemy.orm import Session as OrmSession

from app.models.session import Session as SessionModel
from app.models.session_audit_log import SessionAuditLog
from app.models.therapist import Therapist as TherapistModel
from app.models.therapist_availability import TherapistAvailability, TherapistTimeOff
from app.models.predictive_alert import PredictiveAlert
from app.models.automation_audit_entry import AutomationAuditEntry
from app.models.override_log import OverrideLog
from app.services.conflict_detection_service import ConflictDetectionService
from app.services.matching_service import MatchingService
from app.services.session_audit_service import SessionAuditService
from app.services.therapist_performance_service import TherapistPerformanceService

# Tunable scoring weights (sum = 1.0)
ASSIGNMENT_WEIGHTS = {
    "availability": 0.30,
    "reliability": 0.30,
    "performance": 0.25,
    "caseload_balance": 0.15,
}

RESCHEDULE_WEIGHTS = {
    "availability_fit": 0.45,
    "reliability": 0.30,
    "soonest": 0.25,
}

WEEKLY_LOAD_CAP = 20
LOW_RELIABILITY_THRESHOLD = 75.0
MAX_ASSIGNMENT_RECOMMENDATIONS = 5
MAX_RESCHEDULE_OPTIONS = 12
RESCHEDULE_LOOKAHEAD_DAYS = 14
SLOT_STEP_MINUTES = 30

DATA_FLAG_PENALTIES = {
    "missing_availability": 20,
    "missing_reliability": 20,
    "missing_performance": 15,
    "missing_caseload": 10,
    "missing_timeoff": 10,
}

RISK_FLAG_PENALTIES = {
    "overload_risk": 20,
    "predictive_alert": 25,
    "timeoff_proximity": 15,
    "high_cancellation_risk": 20,
    "marketplace_failures": 10,
}


class AutomationSuggestionService:
    def __init__(self, db: OrmSession):
        self.db = db
        self._matching = MatchingService(db)
        self._conflicts = ConflictDetectionService(db)
        self._performance = TherapistPerformanceService(db)
        self._audit = SessionAuditService(db)

    def _automation_actor(self, performed_by: str | None = None) -> str:
        return performed_by or "system:tier1"

    def _create_automation_audit_entry(
        self,
        session_id: str,
        event_type: str,
        recommended_option: dict | None = None,
        recommended_score: float | None = None,
        confidence_score: float | None = None,
        confidence_components: dict | None = None,
        risks: list | None = None,
        data_gaps: list | None = None,
        human_choice: dict | None = None,
        override_reason: str | None = None,
        performed_by: str | None = None,
    ) -> AutomationAuditEntry:
        entry = AutomationAuditEntry(
            session_id=session_id,
            event_type=event_type,
            recommended_option=recommended_option,
            recommended_score=recommended_score,
            confidence_score=confidence_score,
            confidence_components=confidence_components,
            risks=risks or [],
            data_gaps=data_gaps or [],
            human_choice=human_choice,
            override_reason=override_reason,
            performed_by=self._automation_actor(performed_by),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_automation_audit_entries(self, session_id: str) -> list[dict]:
        entries = (
            self.db.query(AutomationAuditEntry)
            .filter(AutomationAuditEntry.session_id == session_id)
            .order_by(AutomationAuditEntry.timestamp.desc())
            .all()
        )
        return [
            {
                "id": entry.id,
                "session_id": entry.session_id,
                "event_type": entry.event_type,
                "recommended_option": entry.recommended_option,
                "recommended_score": entry.recommended_score,
                "confidence_score": entry.confidence_score,
                "confidence_components": entry.confidence_components,
                "risks": entry.risks,
                "data_gaps": entry.data_gaps,
                "human_choice": entry.human_choice,
                "override_reason": entry.override_reason,
                "performed_by": entry.performed_by,
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            }
            for entry in entries
        ]

    def log_manual_action(
        self,
        session_id: str,
        event_type: str,
        human_choice: dict,
        performed_by: str,
        override_reason: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        metadata = metadata or {}
        if event_type not in {"manual_assignment", "manual_reschedule"}:
            return {"success": False, "error": "Invalid event_type"}

        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return {"success": False, "error": "Session not found"}

        entry = self._create_automation_audit_entry(
            session_id=session_id,
            event_type=event_type,
            recommended_option=metadata.get("recommended_option"),
            recommended_score=metadata.get("recommended_score"),
            confidence_score=metadata.get("confidence_score"),
            confidence_components=metadata.get("confidence_components"),
            risks=metadata.get("risks", []),
            data_gaps=metadata.get("data_gaps", []),
            human_choice=human_choice,
            override_reason=override_reason,
            performed_by=performed_by,
        )

        return {
            "success": True,
            "session_id": session_id,
            "event_type": event_type,
            "audit_entry_id": entry.id,
        }

    def _duration_minutes(self, session: SessionModel) -> int:
        start = datetime.combine(session.date, session.start_time)
        end = datetime.combine(session.date, session.end_time)
        return max(0, int((end - start).total_seconds() / 60))

    def _session_view(self, session, **overrides):
        values = {
            "id": session.id,
            "patient_id": getattr(session, "patient_id", None),
            "therapist_id": getattr(session, "therapist_id", None),
            "date": session.date,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "discipline": getattr(session, "discipline", None),
            "status": getattr(session, "status", None),
            "notes": getattr(session, "notes", None),
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def _week_start(self, value: date) -> date:
        return value - timedelta(days=value.weekday())

    def _weekly_session_count(self, therapist_id: str, ref_date: date, exclude_session_id: str) -> int:
        start = self._week_start(ref_date)
        end = start + timedelta(days=6)
        return (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date >= start,
                SessionModel.date <= end,
                SessionModel.id != exclude_session_id,
                SessionModel.status != "canceled",
            )
            .count()
        )

    def _availability_block(self, therapist_id: str, dow: int, start_time: time, end_time: time):
        blocks = (
            self.db.query(TherapistAvailability)
            .filter(
                TherapistAvailability.therapist_id == therapist_id,
                TherapistAvailability.day_of_week == dow,
            )
            .all()
        )
        for block in blocks:
            if block.start_time <= start_time and block.end_time >= end_time:
                return block
        return None

    def _has_time_off(self, therapist_id: str, session_date: date, start_time: time, end_time: time) -> bool:
        start_dt = datetime.combine(session_date, start_time)
        end_dt = datetime.combine(session_date, end_time)
        return (
            self.db.query(TherapistTimeOff)
            .filter(
                TherapistTimeOff.therapist_id == therapist_id,
                TherapistTimeOff.start_datetime < end_dt,
                TherapistTimeOff.end_datetime > start_dt,
            )
            .first()
            is not None
        )

    def _availability_score(self, therapist_id: str, session: SessionModel) -> float:
        block = self._availability_block(
            therapist_id, session.date.weekday(), session.start_time, session.end_time
        )
        if not block:
            return 0.0

        session_minutes = self._duration_minutes(session)
        block_start = datetime.combine(session.date, block.start_time)
        block_end = datetime.combine(session.date, block.end_time)
        block_minutes = max(1, int((block_end - block_start).total_seconds() / 60))

        fit_ratio = session_minutes / block_minutes
        score = (1.0 - abs(fit_ratio - 0.5)) * 100.0
        return round(max(0.0, min(100.0, score)), 2)

    def _performance_reliability_scores(self, therapist_id: str) -> tuple[float, float]:
        profile = self._performance.get_performance_profile(therapist_id, weeks=12)
        if not profile.get("success"):
            return 50.0, 50.0
        return (
            float(profile.get("performance_score", 50.0)),
            float(profile.get("reliability", {}).get("reliability_score", 50.0)),
        )

    def _caseload_balance_score(self, weekly_sessions: int) -> float:
        ratio = min(weekly_sessions / WEEKLY_LOAD_CAP, 1.0)
        return round((1.0 - ratio) * 100.0, 2)

    def _weekly_minutes(self, therapist_id: str, ref_date: date, exclude_session_id: str) -> int:
        week_start = self._week_start(ref_date)
        week_end = week_start + timedelta(days=6)
        sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.therapist_id == therapist_id,
                SessionModel.date >= week_start,
                SessionModel.date <= week_end,
                SessionModel.id != exclude_session_id,
                SessionModel.status != "canceled",
            )
            .all()
        )
        return sum(self._duration_minutes(s) for s in sessions)

    def _weekly_capacity_minutes(self, therapist_id: str, ref_date: date) -> int:
        week_start = self._week_start(ref_date)
        total = 0
        for offset in range(7):
            day = week_start + timedelta(days=offset)
            blocks = (
                self.db.query(TherapistAvailability)
                .filter(
                    TherapistAvailability.therapist_id == therapist_id,
                    TherapistAvailability.day_of_week == day.weekday(),
                )
                .all()
            )
            for block in blocks:
                minutes = int(
                    (
                        datetime.combine(day, block.end_time)
                        - datetime.combine(day, block.start_time)
                    ).total_seconds()
                    / 60
                )
                minutes = max(0, minutes)
                if block.max_minutes is not None:
                    minutes = min(minutes, block.max_minutes)
                total += minutes
        return total

    def _recent_cancellation_count(self, therapist_id: str, session_date: date, days: int = 14) -> int:
        start_dt = datetime.combine(session_date - timedelta(days=days), time.min)
        end_dt = datetime.combine(session_date, time.max)
        return (
            self.db.query(SessionAuditLog)
            .filter(
                SessionAuditLog.action_type == "canceled",
                SessionAuditLog.performed_by == f"therapist:{therapist_id}",
                SessionAuditLog.timestamp >= start_dt,
                SessionAuditLog.timestamp <= end_dt,
            )
            .count()
        )

    def _therapist_in_predictive_alert(self, therapist_id: str, discipline: str, ref_date: date) -> dict:
        alerts = (
            self.db.query(PredictiveAlert)
            .filter(
                PredictiveAlert.resolved == False,
                PredictiveAlert.effective_date >= (ref_date - timedelta(days=14)),
                PredictiveAlert.effective_date <= (ref_date + timedelta(days=14)),
            )
            .all()
        )

        has_therapist_overload = False
        has_discipline_shortage = False

        for alert in alerts:
            alert_type = (alert.type or "").upper()
            message = (alert.message or "").lower()
            metadata = alert.metadata_json or {}

            if (
                alert_type == "THERAPIST_OVERLOADED"
                and (
                    metadata.get("therapist_id") == therapist_id
                    or therapist_id.lower() in message
                )
            ):
                has_therapist_overload = True

            if (
                alert_type == "THERAPIST_SHORTAGE"
                and (
                    metadata.get("discipline", "").upper() == discipline.upper()
                    or discipline.lower() in message
                )
            ):
                has_discipline_shortage = True

        return {
            "therapist_overload": has_therapist_overload,
            "discipline_shortage": has_discipline_shortage,
        }

    def _marketplace_failure_rate(self, therapist_id: str, session_date: date) -> float:
        """
        Approximate therapist match-failure rate using recent override frequency.
        If therapist model provides match_failure_rate, that value should be passed
        via therapist_metrics and will override this proxy.
        """
        start_dt = datetime.combine(session_date - timedelta(days=30), time.min)
        end_dt = datetime.combine(session_date, time.max)

        assigned_count = (
            self.db.query(SessionAuditLog)
            .filter(
                SessionAuditLog.action_type == "assigned",
                SessionAuditLog.timestamp >= start_dt,
                SessionAuditLog.timestamp <= end_dt,
            )
            .count()
        )

        override_logs = (
            self.db.query(SessionAuditLog)
            .filter(
                SessionAuditLog.action_type == "automation_override",
                SessionAuditLog.timestamp >= start_dt,
                SessionAuditLog.timestamp <= end_dt,
            )
            .all()
        )

        therapist_overrides = 0
        for log in override_logs:
            new_values = log.new_values or {}
            if new_values.get("suggested_therapist_id") == therapist_id:
                therapist_overrides += 1

        denominator = max(1, assigned_count)
        return round(therapist_overrides / denominator, 4)

    def detect_risks(self, session, therapist, therapist_metrics):
        """
        Detect Tier 1 risks and penalties for a therapist-session pairing.
        Returns:
          {
            "risks": [...],
            "risk_penalties": {...}
          }
        """
        risks = []
        risk_penalties = {}

        therapist_id = (
            therapist.get("therapist_id")
            if isinstance(therapist, dict)
            else therapist.therapist_id
        )
        discipline = (
            therapist.get("discipline")
            if isinstance(therapist, dict)
            else therapist.discipline
        )

        weekly_minutes = float(therapist_metrics.get("weekly_minutes", 0.0))
        weekly_capacity = float(therapist_metrics.get("weekly_capacity", 0.0))
        reliability_score = float(therapist_metrics.get("reliability_score", 50.0))

        # b. Capacity risks
        if weekly_capacity > 0 and weekly_minutes > (0.90 * weekly_capacity):
            risks.append("Therapist is near weekly capacity.")
            risk_penalties["overload_risk"] = 20
        if weekly_capacity > 0 and weekly_minutes > weekly_capacity:
            risks.append("Therapist is over weekly capacity.")
            risk_penalties["overload_risk"] = 25

        # c. Time-off risks
        session_start = datetime.combine(session.date, session.start_time)
        session_end = datetime.combine(session.date, session.end_time)
        overlapping_timeoff = (
            self.db.query(TherapistTimeOff)
            .filter(
                TherapistTimeOff.therapist_id == therapist_id,
                TherapistTimeOff.start_datetime < session_end,
                TherapistTimeOff.end_datetime > session_start,
            )
            .first()
        )
        if overlapping_timeoff:
            risks.append("Therapist has time off overlapping this session.")
            risk_penalties["timeoff_proximity"] = 15
        else:
            window_start = session_start - timedelta(hours=48)
            window_end = session_start + timedelta(hours=48)
            near_timeoff = (
                self.db.query(TherapistTimeOff)
                .filter(
                    TherapistTimeOff.therapist_id == therapist_id,
                    TherapistTimeOff.start_datetime <= window_end,
                    TherapistTimeOff.end_datetime >= window_start,
                )
                .first()
            )
            if near_timeoff:
                risks.append("Therapist has time off within 48 hours.")
                risk_penalties["timeoff_proximity"] = 10

        # d. Reliability risks
        if reliability_score < 80:
            risks.append(f"Low reliability score ({round(reliability_score, 2)}).")
            risk_penalties["high_cancellation_risk"] = 20

        recent_cancellations = self._recent_cancellation_count(therapist_id, session.date, days=14)
        if recent_cancellations > 2:
            risks.append("Recent cancellation streak detected.")
            # Keep the stronger penalty if already present.
            existing = risk_penalties.get("high_cancellation_risk", 0)
            risk_penalties["high_cancellation_risk"] = max(existing, 15)

        # e. Predictive alerts
        alert_presence = self._therapist_in_predictive_alert(therapist_id, discipline, session.date)
        if alert_presence["therapist_overload"]:
            risks.append("Predictive alert: therapist overload risk.")
            risk_penalties["predictive_alert"] = 25
        elif alert_presence["discipline_shortage"]:
            risks.append("Predictive alert: discipline shortage.")
            risk_penalties["predictive_alert"] = 15

        # f. Marketplace failures
        metrics_failure_rate = therapist_metrics.get("match_failure_rate")
        if metrics_failure_rate is None:
            model_failure_rate = (
                therapist.get("match_failure_rate")
                if isinstance(therapist, dict)
                else getattr(therapist, "match_failure_rate", None)
            )
            failure_rate = model_failure_rate
        else:
            failure_rate = metrics_failure_rate

        if failure_rate is None:
            failure_rate = self._marketplace_failure_rate(therapist_id, session.date)

        if float(failure_rate) > 0.20:
            risks.append("Therapist frequently fails auto-assignment.")
            risk_penalties["marketplace_failures"] = 10

        return {
            "risks": risks,
            "risk_penalties": risk_penalties,
        }

    def _assignment_confidence(self, top_score: float, second_score: float | None) -> float:
        if second_score is None:
            return round(max(0.0, min(100.0, top_score * 0.9)), 2)
        margin = max(0.0, top_score - second_score)
        # confidence balances absolute quality and winner margin
        confidence = (top_score * 0.75) + (min(margin, 25.0) * 1.0)
        return round(max(0.0, min(100.0, confidence)), 2)

    def compute_confidence(
        self,
        top_score: float,
        second_score: float | None,
        data_flags: dict,
        risk_flags: dict,
    ) -> dict:
        """
        Tier 1 confidence model.

        Returns:
          {
            "confidence": <0.00 - 1.00>,
            "components": {
              "match_quality": <0-100>,
              "candidate_spread": <0-100>,
              "data_completeness": <0-100>,
              "risk_adjustment": <0-100>
            }
          }
        """
        # a. Match Quality (MQ)
        mq = round(max(0.0, min(100.0, top_score)), 2)

        # b. Candidate Spread (CS)
        if second_score is None:
            cs = 100.0
        elif top_score <= 0:
            cs = 0.0
        else:
            cs = 100.0 * (1.0 - (second_score / top_score))
        cs = round(max(0.0, min(100.0, cs)), 2)

        # c. Data Completeness (DC)
        dc_penalty = sum(data_flags.values()) if data_flags else 0
        dc = round(max(0.0, min(100.0, 100.0 - dc_penalty)), 2)

        # d. Risk Adjustment (RA)
        ra_penalty = sum(risk_flags.values()) if risk_flags else 0
        ra = round(max(0.0, min(100.0, 100.0 - ra_penalty)), 2)

        # e. Final confidence score
        confidence = ((0.50 * mq) + (0.20 * cs) + (0.15 * dc) + (0.15 * ra)) / 100.0

        return {
            "confidence": round(max(0.0, min(1.0, confidence)), 2),
            "components": {
                "match_quality": mq,
                "candidate_spread": cs,
                "data_completeness": dc,
                "risk_adjustment": ra,
            },
        }

    def _therapist_risks(
        self,
        therapist_id: str,
        session: SessionModel,
        reliability_score: float,
        weekly_sessions: int,
    ) -> list[str]:
        risks: list[str] = []
        if reliability_score < LOW_RELIABILITY_THRESHOLD:
            risks.append("low_reliability")

        if weekly_sessions >= int(WEEKLY_LOAD_CAP * 0.85):
            risks.append("high_caseload")

        if self._has_time_off(therapist_id, session.date, session.start_time, session.end_time):
            risks.append("time_off_overlap")

        return risks

    def _risk_flag_message(self, risk_flag: str) -> str:
        mapping = {
            "overload_risk": "Near weekly capacity",
            "predictive_alert": "Recent predictive alert indicates elevated scheduling risk",
            "timeoff_proximity": "Time-off proximity may reduce schedule stability",
            "high_cancellation_risk": "Higher cancellation risk based on reliability history",
            "marketplace_failures": "Recent marketplace matching friction observed",
            "high_caseload": "Near weekly capacity",
            "low_reliability": "Reliability score is below preferred threshold",
            "time_off_overlap": "Time-off overlap risk is present",
            "conflict_detected": "Potential scheduling conflict was detected",
            "single_candidate": "Only one viable candidate was identified",
            "low_confidence": "Overall model confidence is low",
            "capacity_constraints": "Capacity constraints are limiting options",
            "no_eligible_therapists": "No eligible therapists matched hard constraints",
            "no_viable_recommendations": "No conflict-free recommendation was available",
        }
        return mapping.get(risk_flag, risk_flag.replace("_", " ").capitalize())

    def _data_flag_message(self, data_flag: str) -> str:
        mapping = {
            "missing_availability": "Availability data is missing or incomplete",
            "missing_reliability": "Reliability data is missing",
            "missing_performance": "Performance data is missing",
            "missing_caseload": "Caseload history data is missing",
            "missing_timeoff": "Time-off data is missing",
        }
        return mapping.get(data_flag, data_flag.replace("_", " ").capitalize())

    def generate_therapist_explanation(self, therapist, scores, risks, data_flags):
        """
        therapist: therapist model or dict (id, name, discipline, etc.)
        scores: dict with availability_score, reliability_score, performance_score,
                caseload_balance_score, total_score, rank
        risks: list of risk flags for this therapist
        data_flags: dict of missing_* booleans for this therapist
        Returns: explanation (string), risk_messages (list), data_gap_messages (list)
        """
        name = therapist.get("name") if isinstance(therapist, dict) else getattr(therapist, "name", "Therapist")
        rank = int(scores.get("rank", 1))
        is_top = rank == 1

        availability = round(float(scores.get("availability_score", 0.0)), 2)
        reliability = round(float(scores.get("reliability_score", 0.0)), 2)
        performance = round(float(scores.get("performance_score", 0.0)), 2)
        caseload = round(float(scores.get("caseload_balance_score", 0.0)), 2)
        total_score = round(float(scores.get("total_score", 0.0)), 2)

        intro = "Top recommendation" if is_top else "Viable alternative"
        explanation = (
            f"{intro}: {name} scored {total_score} with availability {availability}, "
            f"reliability {reliability}, performance {performance}, and caseload balance {caseload}."
        )

        risk_messages = []
        for risk in risks:
            if isinstance(risk, str) and " " in risk:
                risk_messages.append(risk)
            else:
                risk_messages.append(self._risk_flag_message(str(risk)))
        data_gap_messages = [
            self._data_flag_message(flag)
            for flag, missing in data_flags.items()
            if missing
        ]

        if risk_messages:
            explanation += " Risks: " + "; ".join(risk_messages) + "."
        if data_gap_messages:
            explanation += " Data gaps: " + "; ".join(data_gap_messages) + "."

        return explanation, risk_messages, data_gap_messages

    def generate_summary_explanation(self, recommendations, confidence_components, global_risks, data_flags):
        """
        recommendations: sorted list of recommendation dicts
        confidence_components: dict with match_quality, candidate_spread,
                               data_completeness, risk_adjustment
        global_risks: list of global risk messages
        data_flags: aggregated data gaps
        Returns: summary_explanation (string)
        """
        if not recommendations:
            return (
                "No recommendation could be produced because available candidates did not satisfy conflict and "
                "capacity constraints. Manual scheduler review is required."
            )

        mq = float(confidence_components.get("match_quality", 0.0))
        cs = float(confidence_components.get("candidate_spread", 0.0))
        dc = float(confidence_components.get("data_completeness", 0.0))
        ra = float(confidence_components.get("risk_adjustment", 0.0))

        confidence_estimate = ((0.50 * mq) + (0.20 * cs) + (0.15 * dc) + (0.15 * ra)) / 100.0
        if confidence_estimate >= 0.75:
            confidence_label = "high"
            confidence_text = "High confidence due to strong match quality and clear separation from alternatives."
        elif confidence_estimate >= 0.50:
            confidence_label = "medium"
            confidence_text = "Medium confidence with tradeoffs present; scheduler review is recommended."
        else:
            confidence_label = "low"
            confidence_text = "Low confidence driven by risks or data gaps; manual decision is recommended."

        top = recommendations[0]
        top_name = top.get("name", top.get("therapist_id", "top therapist"))
        top_score = top.get("score", 0)

        risk_text = ""
        if global_risks:
            risk_text = " Major risks: " + "; ".join(global_risks) + "."

        gap_messages = [
            self._data_flag_message(flag)
            for flag, penalty in data_flags.items()
            if penalty > 0
        ]
        data_gap_text = ""
        if gap_messages:
            data_gap_text = " Data gaps: " + "; ".join(gap_messages) + "."

        return (
            f"Confidence is {confidence_label}. {confidence_text} "
            f"Top therapist is {top_name} with score {top_score}, standing out on weighted match factors "
            f"(availability, reliability, performance, and caseload balance)."
            f"{risk_text}{data_gap_text}"
        )

    def suggest_assignment(self, session_id: str, performed_by: str | None = None) -> dict:
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return {"success": False, "error": "Session not found"}

        match = self._matching.match_therapists_to_session(session_id)
        if not match:
            return {"success": False, "error": "Session not found"}

        base_ranked = []
        if match.get("best_match"):
            base_ranked.append(match["best_match"])
        base_ranked.extend(match.get("alternatives", []))

        if not base_ranked:
            no_data_flags = {k: v for k, v in DATA_FLAG_PENALTIES.items()}
            no_risk_flags = {
                "overload_risk": 0,
                "predictive_alert": 25,
                "timeoff_proximity": 0,
                "high_cancellation_risk": 0,
                "marketplace_failures": 10,
            }
            confidence_payload = self.compute_confidence(
                top_score=0.0,
                second_score=None,
                data_flags=no_data_flags,
                risk_flags=no_risk_flags,
            )
            response = {
                "success": True,
                "session_id": session_id,
                "recommendations": [],
                "confidence": confidence_payload["confidence"],
                "confidence_components": confidence_payload["components"],
                "data_flags": no_data_flags,
                "risk_flags": no_risk_flags,
                "risks": ["no_eligible_therapists", "capacity_constraints"],
                "global_risks": [
                    self._risk_flag_message("no_eligible_therapists"),
                    self._risk_flag_message("capacity_constraints"),
                ],
                "missing_data": list(no_data_flags.keys()),
                "data_gaps": [self._data_flag_message(flag) for flag in no_data_flags.keys()],
                "summary_explanation": (
                    "No eligible therapists matched hard constraints. Confidence is low due to data gaps and "
                    "limited candidate evidence. Manual scheduler decision is recommended."
                ),
                "explanation": (
                    "No eligible therapists matched discipline, availability, and conflict rules. "
                    "Tier 1 remained in suggestion-only mode and made no assignment changes."
                ),
            }
            self._create_automation_audit_entry(
                session_id=session_id,
                event_type="suggest_assignment",
                recommended_option=None,
                recommended_score=0.0,
                confidence_score=confidence_payload["confidence"],
                confidence_components=confidence_payload["components"],
                risks=response.get("risks", []),
                data_gaps=response.get("data_gaps", []),
                performed_by=performed_by,
            )
            return response

        recommendations = []
        overall_risks = set()
        missing_data = set()

        for candidate in base_ranked[:MAX_ASSIGNMENT_RECOMMENDATIONS]:
            therapist_id = candidate["therapist_id"]
            therapist = (
                self.db.query(TherapistModel)
                .filter(TherapistModel.therapist_id == therapist_id)
                .first()
            )
            if not therapist:
                continue

            # Explicit conflict verification for explainability
            original_therapist = session.therapist_id
            session.therapist_id = therapist_id
            conflict_report = self._conflicts.detect_conflicts_for_session(session_id)
            session.therapist_id = original_therapist
            self.db.expire(session)

            if conflict_report and conflict_report.get("has_conflicts"):
                # MatchingService should have filtered these out, but guard defensively.
                overall_risks.add("conflict_detected")
                continue

            availability_score = self._availability_score(therapist_id, session)
            if availability_score <= 0:
                missing_data.add("missing_availability")

            profile = self._performance.get_performance_profile(therapist_id, weeks=12)
            if not profile.get("success"):
                performance_score, reliability_score = 50.0, 50.0
                missing_data.add("missing_performance")
                missing_data.add("missing_reliability")
                missing_data.add("missing_caseload")
            else:
                performance_score = float(profile.get("performance_score", 50.0))
                reliability_score = float(profile.get("reliability", {}).get("reliability_score", 50.0))

                if profile.get("performance_score") is None:
                    missing_data.add("missing_performance")
                if profile.get("reliability", {}).get("reliability_score") is None:
                    missing_data.add("missing_reliability")

            weekly_sessions = self._weekly_session_count(therapist_id, session.date, session.id)
            caseload_balance_score = self._caseload_balance_score(weekly_sessions)
            if weekly_sessions is None:
                missing_data.add("missing_caseload")

            # time-off data completeness guard
            if therapist_id and self.db.query(TherapistTimeOff).filter(TherapistTimeOff.therapist_id == therapist_id).first() is None:
                missing_data.add("missing_timeoff")

            final_score = round(
                availability_score * ASSIGNMENT_WEIGHTS["availability"]
                + reliability_score * ASSIGNMENT_WEIGHTS["reliability"]
                + performance_score * ASSIGNMENT_WEIGHTS["performance"]
                + caseload_balance_score * ASSIGNMENT_WEIGHTS["caseload_balance"],
                2,
            )

            weekly_minutes = self._weekly_minutes(therapist_id, session.date, session.id)
            weekly_capacity = self._weekly_capacity_minutes(therapist_id, session.date)
            therapist_metrics = {
                "availability_score": availability_score,
                "reliability_score": reliability_score,
                "performance_score": performance_score,
                "caseload_balance_score": caseload_balance_score,
                "weekly_minutes": weekly_minutes,
                "weekly_capacity": weekly_capacity,
            }
            risk_info = self.detect_risks(session, therapist, therapist_metrics)
            risks = risk_info["risks"]
            risk_penalties = risk_info["risk_penalties"]

            for risk in risks:
                overall_risks.add(risk)

            explanation = (
                f"{therapist.first_name} {therapist.last_name} is eligible for this {session.discipline} session. "
                f"Availability fit is {availability_score}, reliability is {reliability_score}, "
                f"performance is {performance_score}, and caseload balance is {caseload_balance_score} "
                f"with {weekly_sessions} sessions this week."
            )

            recommendations.append(
                {
                    "therapist_id": therapist_id,
                    "name": f"{therapist.first_name} {therapist.last_name}",
                    "discipline": therapist.discipline,
                    "score": final_score,
                    "score_breakdown": {
                        "availability_score": availability_score,
                        "reliability_score": reliability_score,
                        "performance_score": performance_score,
                        "caseload_balance_score": caseload_balance_score,
                        "weights": ASSIGNMENT_WEIGHTS,
                    },
                    "risks": risks,
                    "risk_penalties": risk_penalties,
                    "explanation": explanation,
                }
            )

        recommendations.sort(key=lambda r: r["score"], reverse=True)

        if not recommendations:
            no_data_flags = {k: v for k, v in DATA_FLAG_PENALTIES.items() if k in missing_data}
            combined_risks = sorted(list(overall_risks | {"no_viable_recommendations"}))
            no_risk_flags = {
                "overload_risk": 20 if any("capacity" in str(r).lower() for r in combined_risks) else 0,
                "predictive_alert": 25 if any("predictive alert" in str(r).lower() for r in combined_risks) else 0,
                "timeoff_proximity": 15 if any("time off" in str(r).lower() for r in combined_risks) else 0,
                "high_cancellation_risk": 20 if any("cancellation" in str(r).lower() or "reliability" in str(r).lower() for r in combined_risks) else 0,
                "marketplace_failures": 10 if any("marketplace" in str(r).lower() for r in combined_risks) else 0,
            }
            confidence_payload = self.compute_confidence(
                top_score=0.0,
                second_score=None,
                data_flags=no_data_flags,
                risk_flags=no_risk_flags,
            )
            response = {
                "success": True,
                "session_id": session_id,
                "recommendations": [],
                "confidence": confidence_payload["confidence"],
                "confidence_components": confidence_payload["components"],
                "data_flags": no_data_flags,
                "risk_flags": no_risk_flags,
                "risks": combined_risks,
                "global_risks": [self._risk_flag_message(r) for r in combined_risks],
                "missing_data": sorted(list(missing_data)),
                "data_gaps": [self._data_flag_message(flag) for flag in sorted(list(missing_data))],
                "summary_explanation": (
                    "No conflict-free recommendation is available. Confidence is low and manual scheduling "
                    "review is required."
                ),
                "explanation": (
                    "Candidates existed but no conflict-free recommendation could be produced. "
                    "Tier 1 remained in suggestion-only mode with no automatic assignment."
                ),
            }
            self._create_automation_audit_entry(
                session_id=session_id,
                event_type="suggest_assignment",
                recommended_option=None,
                recommended_score=0.0,
                confidence_score=confidence_payload["confidence"],
                confidence_components=confidence_payload["components"],
                risks=response.get("risks", []),
                data_gaps=response.get("data_gaps", []),
                performed_by=performed_by,
            )
            return response

        top = recommendations[0]
        second = recommendations[1]["score"] if len(recommendations) > 1 else None
        data_flags = {
            "missing_availability": DATA_FLAG_PENALTIES["missing_availability"] if "missing_availability" in missing_data else 0,
            "missing_reliability": DATA_FLAG_PENALTIES["missing_reliability"] if "missing_reliability" in missing_data else 0,
            "missing_performance": DATA_FLAG_PENALTIES["missing_performance"] if "missing_performance" in missing_data else 0,
            "missing_caseload": DATA_FLAG_PENALTIES["missing_caseload"] if "missing_caseload" in missing_data else 0,
            "missing_timeoff": DATA_FLAG_PENALTIES["missing_timeoff"] if "missing_timeoff" in missing_data else 0,
        }
        risk_flags = {
            "overload_risk": 0,
            "predictive_alert": 0,
            "timeoff_proximity": 0,
            "high_cancellation_risk": 0,
            "marketplace_failures": 0,
        }

        # Aggregate risk penalties across candidate recommendations (max per risk type).
        for rec in recommendations:
            rec_penalties = rec.get("risk_penalties", {})
            for key in risk_flags.keys():
                risk_flags[key] = max(risk_flags[key], int(rec_penalties.get(key, 0)))
        confidence_payload = self.compute_confidence(
            top_score=top["score"],
            second_score=second,
            data_flags=data_flags,
            risk_flags=risk_flags,
        )
        confidence = confidence_payload["confidence"]

        if confidence < 0.60:
            overall_risks.add("Overall model confidence is low")
        if len(recommendations) == 1:
            overall_risks.add("Only one viable candidate was identified")

        # Per-therapist explainability pass with risk and data-gap messages.
        for idx, rec in enumerate(recommendations):
            therapist_data_flags = {
                "missing_availability": rec["score_breakdown"].get("availability_score", 0) <= 0,
                "missing_reliability": rec["score_breakdown"].get("reliability_score", 0) <= 0,
                "missing_performance": rec["score_breakdown"].get("performance_score", 0) <= 0,
                "missing_caseload": rec["score_breakdown"].get("caseload_balance_score", 0) <= 0,
                "missing_timeoff": "missing_timeoff" in missing_data,
            }
            scores = {
                "availability_score": rec["score_breakdown"].get("availability_score", 0),
                "reliability_score": rec["score_breakdown"].get("reliability_score", 0),
                "performance_score": rec["score_breakdown"].get("performance_score", 0),
                "caseload_balance_score": rec["score_breakdown"].get("caseload_balance_score", 0),
                "total_score": rec.get("score", 0),
                "rank": idx + 1,
            }
            rec_explanation, rec_risk_messages, rec_data_gap_messages = self.generate_therapist_explanation(
                therapist={
                    "id": rec.get("therapist_id"),
                    "name": rec.get("name"),
                    "discipline": rec.get("discipline"),
                },
                scores=scores,
                risks=rec.get("risks", []),
                data_flags=therapist_data_flags,
            )
            rec["risk_flags"] = list(rec.get("risk_penalties", {}).keys())
            rec["risks"] = rec_risk_messages
            rec["data_flags"] = therapist_data_flags
            rec["data_gaps"] = rec_data_gap_messages
            rec["explanation"] = rec_explanation

        global_risk_messages = []
        for risk in sorted(list(overall_risks)):
            if isinstance(risk, str) and " " in risk:
                global_risk_messages.append(risk)
            else:
                global_risk_messages.append(self._risk_flag_message(str(risk)))
        summary_explanation = self.generate_summary_explanation(
            recommendations=recommendations,
            confidence_components=confidence_payload["components"],
            global_risks=global_risk_messages,
            data_flags=data_flags,
        )

        response = {
            "success": True,
            "session_id": session_id,
            "recommendations": recommendations,
            "confidence": confidence,
            "confidence_components": confidence_payload["components"],
            "data_flags": data_flags,
            "risk_flags": risk_flags,
            "risks": sorted(list(overall_risks)),
            "global_risks": global_risk_messages,
            "missing_data": sorted([k for k, v in data_flags.items() if v > 0]),
            "data_gaps": [self._data_flag_message(k) for k, v in data_flags.items() if v > 0],
            "summary_explanation": summary_explanation,
            "explanation": (
                f"Top recommendation is therapist {top['therapist_id']} because they produced the strongest "
                f"weighted match score ({top['score']}) across availability, reliability, performance, and caseload balance. "
                f"Final Tier 1 confidence is {confidence} (0-1 scale). No assignment has been applied."
            ),
        }
        self._create_automation_audit_entry(
            session_id=session_id,
            event_type="suggest_assignment",
            recommended_option=top,
            recommended_score=top.get("score"),
            confidence_score=confidence,
            confidence_components=confidence_payload["components"],
            risks=sorted(list(overall_risks)),
            data_gaps=response.get("data_gaps", []),
            performed_by=performed_by,
        )
        return response

    def _candidate_start_times(self, block_start: time, block_end: time, duration_minutes: int) -> list[time]:
        starts: list[time] = []
        ref = date.today()
        cursor = datetime.combine(ref, block_start)
        block_end_dt = datetime.combine(ref, block_end)
        while cursor + timedelta(minutes=duration_minutes) <= block_end_dt:
            starts.append(cursor.time())
            cursor += timedelta(minutes=SLOT_STEP_MINUTES)
        return starts

    def generate_candidate_slots(self, session: SessionModel, therapist: TherapistModel) -> list[dict]:
        session_minutes = self._duration_minutes(session)
        if session_minutes <= 0:
            return []

        therapist_id = therapist.therapist_id
        today = date.today()
        candidate_slots: list[dict] = []

        for offset in range(0, RESCHEDULE_LOOKAHEAD_DAYS + 1):
            day = today + timedelta(days=offset)
            blocks = (
                self.db.query(TherapistAvailability)
                .filter(
                    TherapistAvailability.therapist_id == therapist_id,
                    TherapistAvailability.day_of_week == day.weekday(),
                )
                .all()
            )
            if not blocks:
                continue

            for block in blocks:
                for start_t in self._candidate_start_times(
                    block.start_time, block.end_time, session_minutes
                ):
                    end_t = (
                        datetime.combine(day, start_t) + timedelta(minutes=session_minutes)
                    ).time()

                    if self._has_time_off(therapist_id, day, start_t, end_t):
                        continue

                    candidate_session = self._session_view(
                        session,
                        date=day,
                        start_time=start_t,
                        end_time=end_t,
                        therapist_id=therapist_id,
                    )
                    if self._conflicts.has_any_conflict(therapist_id, candidate_session):
                        continue

                    candidate_slots.append(
                        {
                            "date": day,
                            "start_time": start_t,
                            "end_time": end_t,
                        }
                    )

        return candidate_slots

    def score_reschedule_slot(
        self, session: SessionModel, therapist: TherapistModel, slot: dict
    ) -> dict:
        weights = {
            "availability_fit_score": 0.40,
            "conflict_risk_score": 0.30,
            "caseload_balance_score": 0.15,
            "reliability_performance_score": 0.15,
        }

        session_view = self._session_view(
            session,
            date=slot["date"],
            start_time=slot["start_time"],
            end_time=slot["end_time"],
            therapist_id=therapist.therapist_id,
        )

        availability_fit_score = self._availability_score(therapist.therapist_id, session_view)

        conflict_risk_score = (
            0.0 if self._conflicts.has_any_conflict(therapist.therapist_id, session_view) else 100.0
        )

        projected_weekly_sessions = (
            self._weekly_session_count(therapist.therapist_id, slot["date"], session_view.id) + 1
        )
        caseload_balance_score = self._caseload_balance_score(projected_weekly_sessions)

        perf_score, rel_score = self._performance_reliability_scores(therapist.therapist_id)
        reliability_performance_score = round((perf_score + rel_score) / 2.0, 2)

        total_score = round(
            availability_fit_score * weights["availability_fit_score"]
            + conflict_risk_score * weights["conflict_risk_score"]
            + caseload_balance_score * weights["caseload_balance_score"]
            + reliability_performance_score * weights["reliability_performance_score"],
            2,
        )

        return {
            "total_score": max(0.0, min(100.0, total_score)),
            "availability_fit_score": round(availability_fit_score, 2),
            "conflict_risk_score": round(conflict_risk_score, 2),
            "caseload_balance_score": round(caseload_balance_score, 2),
            "reliability_performance_score": round(reliability_performance_score, 2),
        }

    def suggest_reschedule(self, session_id: str, performed_by: str | None = None) -> dict:
        session = None
        try:
            with self.db.no_autoflush:
                session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
                if not session:
                    return {"success": False, "error": "Session not found"}

                session_view = self._session_view(session)
                session_minutes = self._duration_minutes(session_view)
                if session_minutes <= 0:
                    return {"success": False, "error": "Session duration must be positive"}

                therapist_pool: list[str] = []
                if session_view.therapist_id:
                    therapist_pool.append(session_view.therapist_id)

                match = self._matching.match_therapists_to_session(session_id)
                if match:
                    ranked = []
                    if match.get("best_match"):
                        ranked.append(match["best_match"])
                    ranked.extend(match.get("alternatives", []))
                    for candidate in ranked[:3]:
                        t_id = candidate["therapist_id"]
                        if t_id not in therapist_pool:
                            therapist_pool.append(t_id)

                if not therapist_pool:
                    return {
                        "success": True,
                        "session_id": session_id,
                        "current_time": datetime.utcnow().isoformat() + "Z",
                        "recommendations": [],
                        "confidence": 0.0,
                        "confidence_components": {
                            "match_quality": 0.0,
                            "candidate_spread": 0.0,
                            "data_completeness": 100.0,
                            "risk_adjustment": 100.0,
                        },
                        "summary_explanation": "No therapist pool available to suggest alternative times.",
                        "global_risks": [self._risk_flag_message("no_eligible_therapists")],
                    }

                recommendations = []
                overall_risks = set()
                missing_data = set()

                for t_id in therapist_pool:
                    therapist = (
                        self.db.query(TherapistModel)
                        .filter(TherapistModel.therapist_id == t_id)
                        .first()
                    )
                    if not therapist:
                        continue

                    perf_score, rel_score = self._performance_reliability_scores(t_id)
                    if t_id and self.db.query(TherapistTimeOff).filter(TherapistTimeOff.therapist_id == t_id).first() is None:
                        missing_data.add("missing_timeoff")

                    candidate_slots = self.generate_candidate_slots(session_view, therapist)
                    for slot in candidate_slots:
                        day = slot["date"]
                        start_t = slot["start_time"]
                        end_t = slot["end_time"]

                        slot_session = self._session_view(
                            session_view,
                            date=day,
                            start_time=start_t,
                            end_time=end_t,
                            therapist_id=t_id,
                        )

                        slot_scores = self.score_reschedule_slot(session_view, therapist, slot)
                        total_score = slot_scores["total_score"]

                        weekly_minutes = self._weekly_minutes(t_id, day, session_view.id) + session_minutes
                        weekly_capacity = self._weekly_capacity_minutes(t_id, day)
                        therapist_metrics = {
                            "availability_score": slot_scores["availability_fit_score"],
                            "reliability_score": rel_score,
                            "performance_score": perf_score,
                            "caseload_balance_score": slot_scores["caseload_balance_score"],
                            "weekly_minutes": weekly_minutes,
                            "weekly_capacity": weekly_capacity,
                        }
                        risk_info = self.detect_risks(slot_session, therapist, therapist_metrics)
                        slot_risks = risk_info["risks"]
                        slot_risk_penalties = risk_info["risk_penalties"]

                        for risk in slot_risks:
                            overall_risks.add(risk)

                        therapist_data_flags = {
                            "missing_availability": slot_scores["availability_fit_score"] <= 0,
                            "missing_reliability": slot_scores["reliability_performance_score"] <= 0,
                            "missing_performance": slot_scores["reliability_performance_score"] <= 0,
                            "missing_caseload": slot_scores["caseload_balance_score"] <= 0,
                            "missing_timeoff": "missing_timeoff" in missing_data,
                        }

                        for flag, missing in therapist_data_flags.items():
                            if missing:
                                missing_data.add(flag)

                        recommendations.append(
                            {
                                "therapist_id": t_id,
                                "name": f"{therapist.first_name} {therapist.last_name}",
                                "discipline": therapist.discipline,
                                "date": day.isoformat(),
                                "start_time": start_t.isoformat(),
                                "end_time": end_t.isoformat(),
                                "score": total_score,
                                "score_breakdown": {
                                    "availability_fit_score": slot_scores["availability_fit_score"],
                                    "conflict_risk_score": slot_scores["conflict_risk_score"],
                                    "caseload_balance_score": slot_scores["caseload_balance_score"],
                                    "reliability_performance_score": slot_scores[
                                        "reliability_performance_score"
                                    ],
                                },
                                "risk_penalties": slot_risk_penalties,
                                "risks": slot_risks,
                                "data_flags": therapist_data_flags,
                            }
                        )

                recommendations.sort(key=lambda r: r["score"], reverse=True)
                recommendations = recommendations[:MAX_RESCHEDULE_OPTIONS]

                if not recommendations:
                    no_data_flags = {
                        k: DATA_FLAG_PENALTIES[k]
                        for k in DATA_FLAG_PENALTIES.keys()
                        if k in missing_data
                    }
                    no_risk_flags = {
                        "overload_risk": 0,
                        "predictive_alert": 0,
                        "timeoff_proximity": 0,
                        "high_cancellation_risk": 0,
                        "marketplace_failures": 0,
                    }
                    confidence_payload = self.compute_confidence(
                        top_score=0.0,
                        second_score=None,
                        data_flags=no_data_flags,
                        risk_flags=no_risk_flags,
                    )
                    global_risk_messages = [self._risk_flag_message("no_viable_recommendations")]
                    return {
                        "success": True,
                        "session_id": session_id,
                        "current_time": datetime.utcnow().isoformat() + "Z",
                        "recommendations": [],
                        "confidence": confidence_payload["confidence"],
                        "confidence_components": confidence_payload["components"],
                        "summary_explanation": (
                            "No conflict-free reschedule options were found in the lookahead window. "
                            "Tier 1 remained in suggestion-only mode and applied no schedule change."
                        ),
                        "global_risks": global_risk_messages,
                    }

                top_score = recommendations[0]["score"]
                second_score = recommendations[1]["score"] if len(recommendations) > 1 else None

                data_flags = {
                    "missing_availability": DATA_FLAG_PENALTIES["missing_availability"] if "missing_availability" in missing_data else 0,
                    "missing_reliability": DATA_FLAG_PENALTIES["missing_reliability"] if "missing_reliability" in missing_data else 0,
                    "missing_performance": DATA_FLAG_PENALTIES["missing_performance"] if "missing_performance" in missing_data else 0,
                    "missing_caseload": DATA_FLAG_PENALTIES["missing_caseload"] if "missing_caseload" in missing_data else 0,
                    "missing_timeoff": DATA_FLAG_PENALTIES["missing_timeoff"] if "missing_timeoff" in missing_data else 0,
                }
                risk_flags = {
                    "overload_risk": 0,
                    "predictive_alert": 0,
                    "timeoff_proximity": 0,
                    "high_cancellation_risk": 0,
                    "marketplace_failures": 0,
                }

                for rec in recommendations:
                    penalties = rec.get("risk_penalties", {})
                    for key in risk_flags.keys():
                        risk_flags[key] = max(risk_flags[key], int(penalties.get(key, 0)))

                confidence_payload = self.compute_confidence(
                    top_score=top_score,
                    second_score=second_score,
                    data_flags=data_flags,
                    risk_flags=risk_flags,
                )
                confidence = confidence_payload["confidence"]

                if confidence < 0.60:
                    overall_risks.add("low_confidence")
                if len(recommendations) == 1:
                    overall_risks.add("single_candidate")

                for idx, rec in enumerate(recommendations):
                    scores = {
                        "availability_score": rec["score_breakdown"].get("availability_fit_score", 0),
                        "reliability_score": rec["score_breakdown"].get("reliability_performance_score", 0),
                        "performance_score": rec["score_breakdown"].get("reliability_performance_score", 0),
                        "caseload_balance_score": rec["score_breakdown"].get("caseload_balance_score", 0),
                        "total_score": rec.get("score", 0),
                        "rank": idx + 1,
                    }
                    rec_explanation, rec_risk_messages, rec_data_gap_messages = self.generate_therapist_explanation(
                        therapist={
                            "id": rec.get("therapist_id"),
                            "name": rec.get("name"),
                            "discipline": rec.get("discipline"),
                        },
                        scores=scores,
                        risks=rec.get("risks", []),
                        data_flags=rec.get("data_flags", {}),
                    )
                    rec["risk_flags"] = list(rec.get("risk_penalties", {}).keys())
                    rec["risks"] = rec_risk_messages
                    rec["data_gaps"] = rec_data_gap_messages
                    rec["explanation"] = rec_explanation

                global_risk_messages = []
                for risk in sorted(list(overall_risks)):
                    if isinstance(risk, str) and " " in risk:
                        global_risk_messages.append(risk)
                    else:
                        global_risk_messages.append(self._risk_flag_message(str(risk)))

                summary_explanation = self.generate_summary_explanation(
                    recommendations=recommendations,
                    confidence_components=confidence_payload["components"],
                    global_risks=global_risk_messages,
                    data_flags=data_flags,
                )

                return {
                    "success": True,
                    "session_id": session_id,
                    "current_time": datetime.utcnow().isoformat() + "Z",
                    "recommendations": recommendations,
                    "confidence": confidence,
                    "confidence_components": confidence_payload["components"],
                    "summary_explanation": summary_explanation,
                    "global_risks": global_risk_messages,
                }
        except Exception as exc:
            return {"success": False, "error": f"suggest_reschedule_failed: {exc}"}
        finally:
            try:
                if self.db.new or self.db.dirty or self.db.deleted:
                    self.db.rollback()
            except Exception:
                pass

    def log_override(
        self,
        session_id: str,
        recommended_therapist_id: str,
        chosen_therapist_id: str,
        reason: str,
        metadata: dict | None = None,
    ) -> dict:
        metadata = metadata or {}
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return {"success": False, "error": "Session not found"}

        therapist = (
            self.db.query(TherapistModel)
            .filter(TherapistModel.therapist_id == chosen_therapist_id)
            .first()
        )
        if not therapist:
            return {"success": False, "error": "Therapist not found"}

        override_row = OverrideLog(
            session_id=session_id,
            recommended_therapist_id=recommended_therapist_id or None,
            chosen_therapist_id=chosen_therapist_id,
            recommended_score=metadata.get("recommended_score"),
            chosen_score=metadata.get("chosen_score"),
            confidence_score=metadata.get("confidence"),
            risk_summary=metadata.get("risks", []),
            data_gaps=metadata.get("data_gaps", []),
            override_reason=reason or "Manual override recorded in suggestion mode",
            overridden_by=metadata.get("overridden_by"),
        )
        self.db.add(override_row)
        self.db.commit()
        self.db.refresh(override_row)

        self._audit.log_action(
            session_id=session_id,
            action_type="automation_override",
            performed_by=(metadata.get("overridden_by") or "scheduler:override"),
            old_values={
                "recommended_therapist_id": recommended_therapist_id,
                "status": session.status,
            },
            new_values={
                "chosen_therapist_id": chosen_therapist_id,
                "session_id": session_id,
                "override_log_id": override_row.id,
            },
            notes=reason or "Manual override recorded in suggestion mode",
        )

        audit_entry = self._create_automation_audit_entry(
            session_id=session_id,
            event_type="override",
            recommended_option={
                "therapist_id": recommended_therapist_id,
                "score": metadata.get("recommended_score"),
            },
            recommended_score=metadata.get("recommended_score"),
            confidence_score=metadata.get("confidence"),
            confidence_components=metadata.get("confidence_components"),
            risks=metadata.get("risks", []),
            data_gaps=metadata.get("data_gaps", []),
            human_choice={
                "therapist_id": chosen_therapist_id,
                "score": metadata.get("chosen_score"),
            },
            override_reason=reason,
            performed_by=metadata.get("overridden_by"),
        )

        return {
            "success": True,
            "session_id": session_id,
            "recommended_therapist_id": recommended_therapist_id,
            "chosen_therapist_id": chosen_therapist_id,
            "reason": reason,
            "override_log_id": override_row.id,
            "automation_audit_entry_id": audit_entry.id,
            "logged": True,
        }
