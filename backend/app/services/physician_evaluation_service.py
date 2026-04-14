from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.orm import Session
from ..models.physician_evaluation import PhysicianEvaluation
from ..compliance_engines.first_day_engine import physician_evaluation_compliance


class PhysicianEvaluationService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_evaluation(
        self,
        patient_id: str,
        physician_id: str,
        evaluation_timestamp: datetime,
        notes: Optional[str] = None,
        source: str = 'manual'
    ) -> PhysicianEvaluation:
        """Create a new physician evaluation."""
        evaluation = PhysicianEvaluation(
            patient_id=patient_id,
            physician_id=physician_id,
            evaluation_datetime=evaluation_timestamp,
            notes=notes,
            source=source
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    def create_physician_evaluation(
        self,
        patient_id: str,
        physician_id: str,
        physician_name: str,
        evaluation_datetime: datetime,
        notes: Optional[str] = None,
        first_day_compliance: Optional[bool] = None,
        **kwargs
    ) -> PhysicianEvaluation:
        """Create a new physician evaluation (modern API)."""
        # Generate evaluation_id if not provided
        evaluation_id = kwargs.get('evaluation_id', f"EVAL-{uuid.uuid4().hex[:12].upper()}")
        
        evaluation = PhysicianEvaluation(
            evaluation_id=evaluation_id,
            patient_id=patient_id,
            physician_id=physician_id,
            physician_name=physician_name,
            evaluation_datetime=evaluation_datetime,
            notes=notes,
            first_day_compliance=first_day_compliance,
            source=kwargs.get('source', 'manual')
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    def get_evaluations_for_patient(self, patient_id: str) -> List[PhysicianEvaluation]:
        """Get all evaluations for a patient."""
        return self.db.query(PhysicianEvaluation).filter(PhysicianEvaluation.patient_id == patient_id).all()

    def get_patient_evaluations(self, patient_id: str) -> List[PhysicianEvaluation]:
        """Get all evaluations for a patient (alias for backward compatibility)."""
        return self.get_evaluations_for_patient(patient_id)

    def check_first_day_compliance(self, patient_id: str) -> bool:
        """Check if patient has first day evaluation compliance.
        
        Returns True if an evaluation exists within 24 hours of admission.
        """
        from datetime import timedelta
        from ..models.patient import Patient
        
        patient = self.db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            return False
        
        latest_eval = self.get_latest_evaluation(patient_id)
        if not latest_eval:
            return False
        
        # Check if evaluation is within 24 hours of admission
        time_diff = latest_eval.evaluation_datetime - patient.admission_datetime
        return time_diff.total_seconds() < 86400  # 24 hours in seconds

    def get_latest_evaluation(self, patient_id: str) -> Optional[PhysicianEvaluation]:
        """Get the most recent evaluation for a patient."""
        return self.db.query(PhysicianEvaluation)\
            .filter(PhysicianEvaluation.patient_id == patient_id)\
            .order_by(PhysicianEvaluation.evaluation_datetime.desc())\
            .first()

    def get_compliance(self, patient_id: str) -> Dict[str, Any]:
        """Get physician evaluation compliance for a patient."""
        # Get patient's admission datetime
        from ..models.patient import Patient
        patient = self.db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            return {'status': 'Red', 'notes': 'Patient not found'}

        latest_eval = self.get_latest_evaluation(patient_id)
        eval_datetime = latest_eval.evaluation_datetime if latest_eval else None

        return physician_evaluation_compliance(patient.admission_datetime, eval_datetime)

    def update_evaluation(self, evaluation_id: str, **updates) -> Optional[PhysicianEvaluation]:
        """Update evaluation fields."""
        evaluation = self.db.query(PhysicianEvaluation).filter(PhysicianEvaluation.evaluation_id == evaluation_id).first()
        if not evaluation:
            return None

        for key, value in updates.items():
            if hasattr(evaluation, key):
                setattr(evaluation, key, value)

        evaluation.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation