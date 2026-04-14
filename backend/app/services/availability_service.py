import uuid
from datetime import time, datetime
from sqlalchemy.orm import Session as OrmSession
from backend.app.models.therapist_availability import TherapistAvailability, TherapistTimeOff


class AvailabilityService:
    def __init__(self, db: OrmSession):
        self.db = db

    def _parse_time(self, value):
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            return time.fromisoformat(value)
        raise ValueError("Invalid time format; expected HH:MM[:SS]")

    def _parse_datetime(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise ValueError("Invalid datetime format; expected ISO 8601")

    def _serialize_availability(self, block):
        return {
            "id": block.id,
            "therapist_id": block.therapist_id,
            "day_of_week": block.day_of_week,
            "start_time": block.start_time.isoformat(),
            "end_time": block.end_time.isoformat(),
            "max_sessions": block.max_sessions,
            "max_minutes": block.max_minutes,
            "created_at": block.created_at.isoformat() if block.created_at else None,
        }

    def _serialize_time_off(self, block):
        return {
            "id": block.id,
            "therapist_id": block.therapist_id,
            "start_datetime": block.start_datetime.isoformat(),
            "end_datetime": block.end_datetime.isoformat(),
            "reason": block.reason,
        }

    def get_availability_for_therapist(self, therapist_id: str):
        results = (
            self.db.query(TherapistAvailability)
            .filter(TherapistAvailability.therapist_id == therapist_id)
            .order_by(TherapistAvailability.day_of_week.asc(), TherapistAvailability.start_time.asc())
            .all()
        )
        return [self._serialize_availability(block) for block in results]

    def add_availability_block(self, therapist_id: str, data: dict):
        block = TherapistAvailability(
            id=data.get("id") or str(uuid.uuid4()),
            therapist_id=therapist_id,
            day_of_week=data["day_of_week"],
            start_time=self._parse_time(data["start_time"]),
            end_time=self._parse_time(data["end_time"]),
            max_sessions=data.get("max_sessions"),
            max_minutes=data.get("max_minutes"),
        )
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return self._serialize_availability(block)

    def delete_availability_block(self, availability_id: str):
        block = (
            self.db.query(TherapistAvailability)
            .filter(TherapistAvailability.id == availability_id)
            .first()
        )
        if not block:
            return False
        self.db.delete(block)
        self.db.commit()
        return True

    def get_time_off_for_therapist(self, therapist_id: str):
        results = (
            self.db.query(TherapistTimeOff)
            .filter(TherapistTimeOff.therapist_id == therapist_id)
            .order_by(TherapistTimeOff.start_datetime.asc())
            .all()
        )
        return [self._serialize_time_off(block) for block in results]

    def add_time_off_block(self, therapist_id: str, data: dict):
        block = TherapistTimeOff(
            id=data.get("id") or str(uuid.uuid4()),
            therapist_id=therapist_id,
            start_datetime=self._parse_datetime(data["start_datetime"]),
            end_datetime=self._parse_datetime(data["end_datetime"]),
            reason=data.get("reason"),
        )
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return self._serialize_time_off(block)

    def delete_time_off_block(self, time_off_id: str):
        block = (
            self.db.query(TherapistTimeOff)
            .filter(TherapistTimeOff.id == time_off_id)
            .first()
        )
        if not block:
            return False
        self.db.delete(block)
        self.db.commit()
        return True
