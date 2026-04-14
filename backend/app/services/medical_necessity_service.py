from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.medical_necessity_record import MedicalNecessityRecord
from ..compliance_engines.medical_necessity_engine import (
    medical_necessity_documented_today,
    medical_necessity_collection_compliance
)


class MedicalNecessityService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_record(
        self,
        patient_id: str,
        statement: str,
        discipline: str,
        barriers: Optional[str] = None,
        clinical_reasoning: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> MedicalNecessityRecord:
        """Add a new medical necessity record."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        record = MedicalNecessityRecord(
            patient_id=patient_id,
            statement=statement,
            barriers=barriers,
            clinical_reasoning=clinical_reasoning,
            timestamp=timestamp,
            discipline=discipline
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_records_for_patient(self, patient_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[MedicalNecessityRecord]:
        """Get medical necessity records for a patient within date range."""
        query = self.db.query(MedicalNecessityRecord).filter(MedicalNecessityRecord.patient_id == patient_id)
        if start_date:
            query = query.filter(MedicalNecessityRecord.timestamp >= start_date)
        if end_date:
            query = query.filter(MedicalNecessityRecord.timestamp <= end_date)
        return query.order_by(MedicalNecessityRecord.timestamp.desc()).all()

    def get_latest_record(self, patient_id: str) -> Optional[MedicalNecessityRecord]:
        """Get the most recent record for a patient."""
        return self.db.query(MedicalNecessityRecord)\
            .filter(MedicalNecessityRecord.patient_id == patient_id)\
            .order_by(MedicalNecessityRecord.timestamp.desc())\
            .first()

    def get_documented_today(self, patient_id: str, target_date: datetime = None) -> Dict[str, Any]:
        """Check if medical necessity is documented today."""
        records = self.get_records_for_patient(patient_id)
        return medical_necessity_documented_today(records, target_date)

    def get_collection_compliance(self, patient_id: str, days_span: int = 7) -> Dict[str, Any]:
        """Get collection compliance over a period."""
        records = self.get_records_for_patient(patient_id)
        return medical_necessity_collection_compliance(records, days_span)

    def get_medical_necessity_summary(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive medical necessity summary."""
        latest = self.get_latest_record(patient_id)
        today_check = self.get_documented_today(patient_id)
        collection = self.get_collection_compliance(patient_id)

        return {
            'latest_record': latest,
            'documented_today': today_check,
            'collection_compliance': collection
        }