from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session as OrmSession

from app.models.predictive_alert import PredictiveAlert
from app.models.session import Session as SessionModel
from app.models.therapist import Therapist as TherapistModel
from app.models.therapist_availability import TherapistAvailability, TherapistTimeOff
from app.services.notification_service import NotificationService


SHORTAGE_THRESHOLD_MINUTES = 60
OVERLOAD_THRESHOLD_RATIO = 1.10
UNASSIGNED_THRESHOLD_COUNT = 3
TIME_OFF_IMPACT_THRESHOLD = 2
SCHEDULER_ALERT_USER = "scheduler:alerts"


class PredictiveAlertService:
    def __init__(self, db: OrmSession):
        self.db = db
        self.notification_service = NotificationService(db)

    def _duration_minutes(self, start_time, end_time, day: date) -> int:
        start_dt = datetime.combine(day, start_time)
        end_dt = datetime.combine(day, end_time)
        return max(0, int((end_dt - start_dt).total_seconds() / 60))

    def _capacity_minutes_for_block(self, block: TherapistAvailability) -> int:
        ref = date.today()
        block_minutes = self._duration_minutes(block.start_time, block.end_time, ref)
        if block.max_minutes is not None:
            return min(block_minutes, block.max_minutes)
        return block_minutes

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

    def _severity_from_ratio(self, value: float) -> str:
        if value >= 1.4:
            return "critical"
        if value >= 1.15:
            return "warning"
        return "info"

    def _serialize_alert(self, alert: PredictiveAlert) -> dict:
        return {
            "id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "message": alert.message,
            "effective_date": alert.effective_date.isoformat(),
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "resolved": alert.resolved,
            "metadata": alert.metadata_json or {},
        }

    def _create_alert(self, alert_type: str, severity: str, message: str, effective_date: date, metadata: dict | None = None):
        existing = (
            self.db.query(PredictiveAlert)
            .filter(
                PredictiveAlert.type == alert_type,
                PredictiveAlert.effective_date == effective_date,
                PredictiveAlert.message == message,
                PredictiveAlert.resolved == False,
            )
            .first()
        )
        if existing:
            return existing

        alert = PredictiveAlert(
            type=alert_type,
            severity=severity,
            message=message,
            effective_date=effective_date,
            resolved=False,
            metadata_json=metadata or {},
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def _push_scheduler_notification(self, alert: PredictiveAlert) -> bool:
        metadata = alert.metadata_json or {}
        session_ids = metadata.get("session_ids") or []

        session_id = None
        for sid in session_ids:
            session = self.db.query(SessionModel).filter(SessionModel.id == sid).first()
            if session:
                session_id = session.id
                break

        if not session_id:
            candidate = (
                self.db.query(SessionModel)
                .filter(SessionModel.date == alert.effective_date)
                .first()
            )
            if candidate:
                session_id = candidate.id

        if not session_id:
            return False

        self.notification_service.notify_user(
            user_id=SCHEDULER_ALERT_USER,
            session_id=session_id,
            notification_type=f"PREDICTIVE_{alert.type}",
            message=alert.message,
        )
        return True

    def generate_therapist_shortage_alerts(self, start_date: date, end_date: date) -> list:
        alerts = []
        days = []
        cursor = start_date
        while cursor <= end_date:
            days.append(cursor)
            cursor += timedelta(days=1)

        disciplines = [
            row[0]
            for row in self.db.query(TherapistModel.discipline)
            .filter(TherapistModel.active == True)
            .distinct()
            .all()
        ]

        for day in days:
            for discipline in disciplines:
                day_sessions = (
                    self.db.query(SessionModel)
                    .filter(
                        SessionModel.date == day,
                        SessionModel.discipline == discipline,
                        SessionModel.status != "canceled",
                    )
                    .all()
                )
                demand_minutes = sum(
                    self._duration_minutes(s.start_time, s.end_time, s.date)
                    for s in day_sessions
                )

                therapists = (
                    self.db.query(TherapistModel)
                    .filter(
                        TherapistModel.active == True,
                        TherapistModel.discipline == discipline,
                    )
                    .all()
                )

                supply_minutes = 0
                available_therapists = 0
                for therapist in therapists:
                    if self._therapist_on_time_off(therapist.therapist_id, day):
                        continue

                    blocks = (
                        self.db.query(TherapistAvailability)
                        .filter(
                            TherapistAvailability.therapist_id == therapist.therapist_id,
                            TherapistAvailability.day_of_week == day.weekday(),
                        )
                        .all()
                    )
                    block_minutes = sum(self._capacity_minutes_for_block(b) for b in blocks)
                    if block_minutes > 0:
                        available_therapists += 1
                        supply_minutes += block_minutes

                deficit = demand_minutes - supply_minutes
                if deficit >= SHORTAGE_THRESHOLD_MINUTES:
                    ratio = (demand_minutes / supply_minutes) if supply_minutes > 0 else 9.9
                    alert = self._create_alert(
                        alert_type="THERAPIST_SHORTAGE",
                        severity=self._severity_from_ratio(ratio),
                        message=(
                            f"Projected {discipline} shortage on {day.isoformat()}: "
                            f"demand {demand_minutes} min vs supply {supply_minutes} min "
                            f"(deficit {deficit} min)."
                        ),
                        effective_date=day,
                        metadata={
                            "discipline": discipline,
                            "demand_minutes": demand_minutes,
                            "supply_minutes": supply_minutes,
                            "deficit_minutes": deficit,
                            "available_therapists": available_therapists,
                            "threshold_minutes": SHORTAGE_THRESHOLD_MINUTES,
                        },
                    )
                    alerts.append(self._serialize_alert(alert))

        return alerts

    def generate_therapist_overload_alerts(self, start_date: date, end_date: date) -> list:
        alerts = []
        therapists = self.db.query(TherapistModel).filter(TherapistModel.active == True).all()

        for therapist in therapists:
            sessions = (
                self.db.query(SessionModel)
                .filter(
                    SessionModel.therapist_id == therapist.therapist_id,
                    SessionModel.date >= start_date,
                    SessionModel.date <= end_date,
                    SessionModel.status != "canceled",
                )
                .all()
            )
            scheduled_minutes = sum(
                self._duration_minutes(s.start_time, s.end_time, s.date)
                for s in sessions
            )

            capacity_minutes = 0
            day = start_date
            while day <= end_date:
                if not self._therapist_on_time_off(therapist.therapist_id, day):
                    blocks = (
                        self.db.query(TherapistAvailability)
                        .filter(
                            TherapistAvailability.therapist_id == therapist.therapist_id,
                            TherapistAvailability.day_of_week == day.weekday(),
                        )
                        .all()
                    )
                    capacity_minutes += sum(self._capacity_minutes_for_block(b) for b in blocks)
                day += timedelta(days=1)

            if capacity_minutes <= 0:
                if scheduled_minutes <= 0:
                    continue
                load_ratio = 9.9
            else:
                load_ratio = scheduled_minutes / capacity_minutes

            if load_ratio >= OVERLOAD_THRESHOLD_RATIO:
                alert = self._create_alert(
                    alert_type="THERAPIST_OVERLOADED",
                    severity=self._severity_from_ratio(load_ratio),
                    message=(
                        f"Therapist {therapist.therapist_id} is projected over capacity: "
                        f"scheduled {scheduled_minutes} min vs target {capacity_minutes} min."
                    ),
                    effective_date=start_date,
                    metadata={
                        "therapist_id": therapist.therapist_id,
                        "discipline": therapist.discipline,
                        "scheduled_minutes": scheduled_minutes,
                        "target_capacity_minutes": capacity_minutes,
                        "load_ratio": round(load_ratio, 4),
                        "threshold_ratio": OVERLOAD_THRESHOLD_RATIO,
                        "session_count": len(sessions),
                        "session_ids": [s.id for s in sessions],
                    },
                )
                alerts.append(self._serialize_alert(alert))

        return alerts

    def generate_unassigned_session_alerts(self, start_date: date, end_date: date) -> list:
        sessions = (
            self.db.query(SessionModel)
            .filter(
                SessionModel.date >= start_date,
                SessionModel.date <= end_date,
                SessionModel.therapist_id == None,
                SessionModel.status != "canceled",
                SessionModel.status != "completed",
            )
            .all()
        )

        if len(sessions) <= UNASSIGNED_THRESHOLD_COUNT:
            return []

        by_discipline = {}
        for s in sessions:
            by_discipline[s.discipline] = by_discipline.get(s.discipline, 0) + 1

        alert = self._create_alert(
            alert_type="UNASSIGNED_SESSIONS_AT_RISK",
            severity="critical" if len(sessions) >= (UNASSIGNED_THRESHOLD_COUNT * 2) else "warning",
            message=(
                f"{len(sessions)} unassigned sessions detected between "
                f"{start_date.isoformat()} and {end_date.isoformat()}."
            ),
            effective_date=start_date,
            metadata={
                "count": len(sessions),
                "threshold_count": UNASSIGNED_THRESHOLD_COUNT,
                "by_discipline": by_discipline,
                "session_ids": [s.id for s in sessions],
            },
        )

        return [self._serialize_alert(alert)]

    def generate_time_off_impact_alerts(self, start_date: date, end_date: date) -> list:
        alerts = []
        window_start = datetime.combine(start_date, time.min)
        window_end = datetime.combine(end_date + timedelta(days=1), time.min)

        time_off_blocks = (
            self.db.query(TherapistTimeOff)
            .filter(
                TherapistTimeOff.start_datetime < window_end,
                TherapistTimeOff.end_datetime > window_start,
            )
            .all()
        )

        impacted = {}
        for block in time_off_blocks:
            sessions = (
                self.db.query(SessionModel)
                .filter(
                    SessionModel.therapist_id == block.therapist_id,
                    SessionModel.date >= start_date,
                    SessionModel.date <= end_date,
                    SessionModel.status != "canceled",
                )
                .all()
            )

            affected_ids = []
            for session in sessions:
                session_start = datetime.combine(session.date, session.start_time)
                session_end = datetime.combine(session.date, session.end_time)
                overlaps = session_start < block.end_datetime and session_end > block.start_datetime
                if overlaps:
                    affected_ids.append(session.id)

            if not affected_ids:
                continue

            bucket = impacted.setdefault(
                block.therapist_id,
                {
                    "session_ids": set(),
                    "time_off_blocks": 0,
                },
            )
            bucket["session_ids"].update(affected_ids)
            bucket["time_off_blocks"] += 1

        for therapist_id, data in impacted.items():
            affected_count = len(data["session_ids"])
            if affected_count < TIME_OFF_IMPACT_THRESHOLD:
                continue

            therapist = (
                self.db.query(TherapistModel)
                .filter(TherapistModel.therapist_id == therapist_id)
                .first()
            )
            discipline = therapist.discipline if therapist else None

            alert = self._create_alert(
                alert_type="TIME_OFF_IMPACT",
                severity="critical" if affected_count >= (TIME_OFF_IMPACT_THRESHOLD * 2) else "warning",
                message=(
                    f"Time off impact detected for therapist {therapist_id}: "
                    f"{affected_count} sessions may be affected in the selected window."
                ),
                effective_date=start_date,
                metadata={
                    "therapist_id": therapist_id,
                    "discipline": discipline,
                    "affected_sessions_count": affected_count,
                    "threshold_count": TIME_OFF_IMPACT_THRESHOLD,
                    "time_off_blocks": data["time_off_blocks"],
                    "session_ids": sorted(list(data["session_ids"])),
                },
            )
            alerts.append(self._serialize_alert(alert))

        return alerts

    def run_all(self, start_date: date, end_date: date) -> dict:
        created = []
        created.extend(self.generate_therapist_shortage_alerts(start_date, end_date))
        created.extend(self.generate_therapist_overload_alerts(start_date, end_date))
        created.extend(self.generate_unassigned_session_alerts(start_date, end_date))
        created.extend(self.generate_time_off_impact_alerts(start_date, end_date))

        pushed = 0
        for alert_dict in created:
            alert = self.db.query(PredictiveAlert).filter(PredictiveAlert.id == alert_dict["id"]).first()
            if alert and self._push_scheduler_notification(alert):
                pushed += 1

        return {
            "success": True,
            "range": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "created_count": len(created),
            "scheduler_notifications_pushed": pushed,
            "alerts": created,
        }

    def list_alerts(
        self,
        alert_type: str | None = None,
        severity: str | None = None,
        resolved: bool | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list:
        query = self.db.query(PredictiveAlert)

        if alert_type:
            query = query.filter(PredictiveAlert.type == alert_type)
        if severity:
            query = query.filter(PredictiveAlert.severity == severity)
        if resolved is not None:
            query = query.filter(PredictiveAlert.resolved == resolved)
        if start_date:
            query = query.filter(PredictiveAlert.effective_date >= start_date)
        if end_date:
            query = query.filter(PredictiveAlert.effective_date <= end_date)

        alerts = query.order_by(PredictiveAlert.effective_date.desc(), PredictiveAlert.created_at.desc()).all()
        return [self._serialize_alert(a) for a in alerts]

    def resolve_alert(self, alert_id: int) -> dict:
        alert = self.db.query(PredictiveAlert).filter(PredictiveAlert.id == alert_id).first()
        if not alert:
            return {
                "success": False,
                "error": "Alert not found",
            }

        alert.resolved = True
        self.db.commit()
        self.db.refresh(alert)

        return {
            "success": True,
            "data": self._serialize_alert(alert),
        }
