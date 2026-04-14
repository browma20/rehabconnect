from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.functional_score import FunctionalScore
from ..models.patient import Patient
from ..compliance_engines.functional_improvement_engine import (
    calculate_functional_change,
    improvement_rate,
    plateau_detection
)


class FunctionalService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_functional_score(
        self,
        patient_id: str,
        discipline: str,
        score_type: str,
        score_value: int,
        timestamp: Optional[datetime] = None,
        notes: Optional[str] = None,
        source: str = 'manual'
    ) -> FunctionalScore:
        """Add a new functional score."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        score = FunctionalScore(
            patient_id=patient_id,
            discipline=discipline,
            score_type=score_type,
            score_value=score_value,
            timestamp=timestamp,
            notes=notes,
            source=source
        )
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score

    def get_scores_for_patient(self, patient_id: str, score_type: Optional[str] = None) -> List[FunctionalScore]:
        """Get functional scores for a patient, optionally filtered by type."""
        query = self.db.query(FunctionalScore).filter(FunctionalScore.patient_id == patient_id)
        if score_type:
            query = query.filter(FunctionalScore.score_type == score_type)
        return query.order_by(FunctionalScore.timestamp.desc()).all()

    def get_latest_score(self, patient_id: str, score_type: str) -> Optional[FunctionalScore]:
        """Get the most recent score of a specific type."""
        return self.db.query(FunctionalScore)\
            .filter(FunctionalScore.patient_id == patient_id, FunctionalScore.score_type == score_type)\
            .order_by(FunctionalScore.timestamp.desc())\
            .first()

    def get_baseline_score(self, patient_id: str, score_type: str) -> Optional[FunctionalScore]:
        """Get the baseline (first) score of a specific type."""
        return self.db.query(FunctionalScore)\
            .filter(FunctionalScore.patient_id == patient_id, FunctionalScore.score_type == score_type)\
            .order_by(FunctionalScore.timestamp.asc())\
            .first()

    def get_improvement_rate(self, patient_id: str, score_type: str) -> Dict[str, Any]:
        """Calculate improvement rate for a score type."""
        baseline = self.get_baseline_score(patient_id, score_type)
        latest = self.get_latest_score(patient_id, score_type)

        if not baseline or not latest:
            return {'rate': 0.0, 'notes': 'Insufficient data'}

        # Get days since admission
        patient = self.db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            return {'rate': 0.0, 'notes': 'Patient not found'}

        days_since_admission = (latest.timestamp.date() - patient.admission_datetime.date()).days

        rate = improvement_rate(baseline.score_value, latest.score_value, days_since_admission)
        return {'rate': rate, 'baseline': baseline.score_value, 'latest': latest.score_value, 'days': days_since_admission}

    def get_plateau_detection(self, patient_id: str, score_type: str, plateau_days: int = 3) -> Dict[str, Any]:
        """Detect plateaus in functional scores."""
        scores = self.get_scores_for_patient(patient_id, score_type)
        score_history = [{'score_value': s.score_value} for s in scores[-plateau_days:]]  # Last N scores

        return plateau_detection(score_history, plateau_days)

    def get_functional_summary(self, patient_id: str) -> Dict[str, Any]:
        """Get comprehensive functional summary."""
        # Get all score types
        score_types = self.db.query(FunctionalScore.score_type)\
            .filter(FunctionalScore.patient_id == patient_id)\
            .distinct().all()

        summary = {}
        for (score_type,) in score_types:
            improvement = self.get_improvement_rate(patient_id, score_type)
            plateau = self.get_plateau_detection(patient_id, score_type)
            summary[score_type] = {
                'improvement_rate': improvement,
                'plateau': plateau
            }

        return summary