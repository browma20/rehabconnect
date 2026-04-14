from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.patient import Patient


class PatientService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def _parse_date(self, value: Any) -> date:
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        raise ValueError('Invalid date format; expected YYYY-MM-DD')

    def _parse_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        raise ValueError('Invalid datetime format; expected ISO 8601')

    def _parse_optional_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        return self._parse_datetime(value)

    def create_patient(self, **kwargs) -> Patient:
        """Create a new patient."""
        dob_parsed = self._parse_date(kwargs['dob'])
        admission_parsed = self._parse_datetime(kwargs['admission_datetime'])
        discharge_parsed = self._parse_optional_datetime(kwargs.get('discharge_datetime'))

        patient = Patient(
            patient_id=kwargs['patient_id'],
            mrn=kwargs['mrn'],
            first_name=kwargs['first_name'],
            last_name=kwargs['last_name'],
            dob=dob_parsed,
            admission_datetime=admission_parsed,
            discharge_datetime=discharge_parsed,
            primary_diagnosis=kwargs.get('primary_diagnosis'),
            comorbidities=kwargs.get('comorbidities') or [],
            assigned_disciplines=kwargs.get('assigned_disciplines') or []
        )

        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID."""
        return self.db.query(Patient).filter(Patient.patient_id == patient_id).first()

    def get_all_patients(self) -> List[Patient]:
        """Get all patients."""
        return self.db.query(Patient).all()

    def list_patients(self) -> List[Patient]:
        """List all patients."""
        return self.db.query(Patient).all()

    def update_patient(self, patient_id: str, **updates) -> Optional[Patient]:
        """Update patient fields."""
        patient = self.get_patient(patient_id)
        if not patient:
            return None

        if 'dob' in updates and updates['dob'] is not None:
            updates['dob'] = self._parse_date(updates['dob'])
        if 'admission_datetime' in updates and updates['admission_datetime'] is not None:
            updates['admission_datetime'] = self._parse_datetime(updates['admission_datetime'])
        if 'discharge_datetime' in updates:
            updates['discharge_datetime'] = self._parse_optional_datetime(updates.get('discharge_datetime'))
        if 'comorbidities' in updates and updates.get('comorbidities') is None:
            updates['comorbidities'] = []
        if 'assigned_disciplines' in updates and updates.get('assigned_disciplines') is None:
            updates['assigned_disciplines'] = []

        for key, value in updates.items():
            if hasattr(patient, key):
                setattr(patient, key, value)

        patient.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(patient)
        return patient

    def delete_patient(self, patient_id: str) -> bool:
        """Delete patient by ID."""
        patient = self.get_patient(patient_id)
        if not patient:
            return False

        self.db.delete(patient)
        self.db.commit()
        return True

    def get_patients_by_status(self, active_only: bool = True) -> List[Patient]:
        """Get patients filtered by discharge status."""
        query = self.db.query(Patient)
        if active_only:
            query = query.filter(Patient.discharge_datetime.is_(None))
        return query.all()