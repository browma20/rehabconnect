from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.therapy_session import TherapySession
from ..risk_engine.risk_scoring import calculate_patient_risk, calculate_unit_risk_summary
from .therapy_minutes_service import TherapyMinutesService
from .physician_evaluation_service import PhysicianEvaluationService
from .idt_service import IDTService
from .functional_service import FunctionalService
from .medical_necessity_service import MedicalNecessityService


class RiskService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.therapy_service = TherapyMinutesService(db_session)
        self.physician_service = PhysicianEvaluationService(db_session)
        self.idt_service = IDTService(db_session)
        self.functional_service = FunctionalService(db_session)
        self.medical_service = MedicalNecessityService(db_session)

    def get_patient_risk(self, patient_id: str) -> Dict[str, Any]:
        """Calculate comprehensive risk score for a patient."""
        # Gather compliance results from all services
        compliance_results = {}

        # Therapy minutes compliance
        from datetime import date
        today = date.today()
        compliance_results['three_hour_rule'] = self.therapy_service.get_daily_compliance(patient_id, today)
        compliance_results['therapy_start_36h'] = self._get_therapy_start_compliance(patient_id)

        # IDT compliance
        compliance_results['idt_compliance'] = self.idt_service.get_timeliness_compliance(patient_id, today)

        # Functional improvement
        compliance_results['functional_improvement'] = self._get_functional_compliance(patient_id)

        # Medical necessity
        compliance_results['medical_necessity'] = self.medical_service.get_collection_compliance(patient_id)

        # Calculate risk
        return calculate_patient_risk(compliance_results)

    def get_unit_risk_summary(self, patient_ids: List[str]) -> Dict[str, Any]:
        """Calculate unit-level risk summary for multiple patients."""
        patient_risks = [self.get_patient_risk(pid) for pid in patient_ids]
        return calculate_unit_risk_summary(patient_risks)

    def _get_therapy_start_compliance(self, patient_id: str) -> Dict[str, Any]:
        """Get therapy start compliance (first therapy within 36h)."""
        from ..models.patient import Patient
        from ..compliance_engines.first_day_engine import first_therapy_compliance

        patient = self.db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if not patient:
            return {'status': 'Red', 'notes': 'Patient not found'}

        # Get first therapy session
        first_session = self.db.query(TherapySession)\
            .filter(TherapySession.patient_id == patient_id)\
            .order_by(TherapySession.timestamp.asc())\
            .first()

        first_therapy_time = first_session.timestamp if first_session else None
        return first_therapy_compliance(patient.admission_datetime, first_therapy_time)

    def _get_functional_compliance(self, patient_id: str) -> Dict[str, Any]:
        """Get functional improvement compliance."""
        # Simplified: check if improvement rate > 0
        summary = self.functional_service.get_functional_summary(patient_id)
        if not summary:
            return {'status': 'Red', 'notes': 'No functional data'}

        # Check if any score type has positive improvement
        has_improvement = any(
            data['improvement_rate']['rate'] > 0
            for data in summary.values()
            if 'improvement_rate' in data
        )

        status = 'Green' if has_improvement else 'Red'
        return {'status': status, 'has_improvement': has_improvement}

    def get_high_risk_patients(self, threshold: int = 60) -> List[str]:
        """Get patient IDs with risk score above threshold."""
        # This would require querying all patients, but for simplicity, return empty
        # In real implementation, would need to batch calculate or store risk scores
        return []