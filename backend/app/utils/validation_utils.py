from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import uuid
from sqlalchemy.orm import Session
from ..models.therapy_session import TherapySession
from ..models.patient import Patient
from ..compliance_engines.three_hour_rule_engine import (
    daily_3hour_rule,
    seven_day_rolling_intensity,
    missed_minutes_compliance
)


class TherapyMinutesService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_therapy_session(
        self,
        patient_id: str,
        discipline: str,
        delivered_minutes: int,
        scheduled_minutes: Optional[int] = None,
        missed_minutes: Optional[int] = None,
        reason_code: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Add a new therapy session and return compliance status."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        session = TherapySession(
            patient_id=patient_id,
            discipline=discipline,
            delivered_minutes=delivered_minutes,
            scheduled_minutes=scheduled_minutes,
            missed_minutes=missed_minutes,
            reason_code=reason_code,
            timestamp=timestamp,
            source='manual'  # Assuming manual entry for now
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # Calculate compliance
        daily_compliance = self.get_daily_compliance(patient_id, timestamp.date())
        rolling_compliance = self.get_rolling_compliance(patient_id, timestamp.date())

        return {
            'session_id': session.session_id,
            'daily_compliance': daily_compliance,
            'rolling_compliance': rolling_compliance
        }

    def record_therapy_session(
        self,
        patient_id: str,
        discipline: str,
        session_datetime: datetime,
        duration_minutes: int,
        therapist_id: Optional[str] = None,
        treatment_type: Optional[str] = None,
        goals_addressed: Optional[List[str]] = None,
        notes: Optional[str] = None,
        **kwargs
    ) -> TherapySession:
        """Record a therapy session (API format)."""
        # Generate a session_id if not provided
        session_id = kwargs.get('session_id', f"SESSION-{uuid.uuid4().hex[:12].upper()}")
        
        session = TherapySession(
            session_id=session_id,
            patient_id=patient_id,
            discipline=discipline,
            delivered_minutes=duration_minutes,  # Map duration_minutes to delivered_minutes
            timestamp=session_datetime,
            source=kwargs.get('source', 'API'),
            therapist_id=therapist_id
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_patient_sessions(self, patient_id: str) -> List[TherapySession]:
        """Get all therapy sessions for a patient."""
        return self.db.query(TherapySession).filter(TherapySession.patient_id == patient_id).all()

    def get_daily_minutes(self, patient_id: str, target_date: date) -> int:
        """Get total therapy minutes for a patient on a specific date."""
        sessions = self.get_sessions_for_patient(patient_id, target_date, target_date)
        return sum(s.delivered_minutes for s in sessions)

    def get_sessions_for_patient(self, patient_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[TherapySession]:
        """Get therapy sessions for a patient within date range."""
        from datetime import timedelta
        query = self.db.query(TherapySession).filter(TherapySession.patient_id == patient_id)
        if start_date:
            start_dt = datetime.combine(start_date, datetime.min.time())
            query = query.filter(TherapySession.timestamp >= start_dt)
        if end_date:
            end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
            query = query.filter(TherapySession.timestamp < end_dt)
        return query.all()

    def get_daily_compliance(self, patient_id: str, target_date: date) -> Dict[str, Any]:
        """Get daily 3-hour rule compliance for a patient on a specific date."""
        sessions = self.get_sessions_for_patient(patient_id, target_date, target_date)
        total_delivered = sum(s.delivered_minutes for s in sessions)
        total_scheduled = sum(s.scheduled_minutes or 0 for s in sessions)
        total_missed = sum(s.missed_minutes or 0 for s in sessions)
        reason_codes = [s.reason_code for s in sessions if s.reason_code]

        # Use the first reason code if any, or None
        reason_code = reason_codes[0] if reason_codes else None

        return daily_3hour_rule(
            delivered_minutes=total_delivered,
            scheduled_minutes=total_scheduled,
            missed_minutes=total_missed,
            reason_code=reason_code
        )

    def get_rolling_compliance(self, patient_id: str, as_of_date: date) -> Dict[str, Any]:
        """Get 7-day rolling intensity compliance."""
        # Get sessions for the rolling window
        sessions = self.get_sessions_for_patient(patient_id, as_of_date - timedelta(days=6), as_of_date)
        session_data = [{'date': s.timestamp.date(), 'delivered_minutes': s.delivered_minutes} for s in sessions]

        return seven_day_rolling_intensity(session_data, as_of_date)

    def get_missed_minutes_compliance(self, patient_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, Any]:
        """Get missed minutes documentation compliance."""
        sessions = self.get_sessions_for_patient(patient_id, start_date, end_date)
        session_dicts = [
            {
                'missed_minutes': s.missed_minutes or 0,
                'reason_code': s.reason_code
            }
            for s in sessions
        ]
        return missed_minutes_compliance(session_dicts)

    def get_patient_summary(self, patient_id: str, as_of_date: date) -> Dict[str, Any]:
        """Get comprehensive therapy summary for a patient."""
        daily = self.get_daily_compliance(patient_id, as_of_date)
        rolling = self.get_rolling_compliance(patient_id, as_of_date)
        missed = self.get_missed_minutes_compliance(patient_id, as_of_date - timedelta(days=6), as_of_date)

        return {
            'daily_compliance': daily,
            'rolling_compliance': rolling,
            'missed_minutes_compliance': missed,
            'total_sessions_today': len(self.get_sessions_for_patient(patient_id, as_of_date, as_of_date))
        }