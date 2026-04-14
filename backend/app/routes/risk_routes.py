from flask import Blueprint, request, jsonify
from ..services.risk_service import RiskService
from ..database import SessionLocal

risk_bp = Blueprint('risk', __name__)

@risk_bp.route('/patients/<patient_id>/risk', methods=['GET'])
def get_patient_risk(patient_id):
    """Get risk score for a patient."""
    db = SessionLocal()
    try:
        service = RiskService(db)
        risk = service.get_patient_risk(patient_id)
        return jsonify(risk)
    finally:
        db.close()

@risk_bp.route('/unit/risk-summary', methods=['POST'])
def get_unit_risk_summary():
    """Get unit-level risk summary."""
    data = request.get_json()
    patient_ids = data.get('patient_ids', [])

    db = SessionLocal()
    try:
        service = RiskService(db)
        summary = service.get_unit_risk_summary(patient_ids)
        return jsonify(summary)
    finally:
        db.close()

@risk_bp.route('/patients/high-risk', methods=['GET'])
def get_high_risk_patients():
    """Get high-risk patients."""
    threshold = int(request.args.get('threshold', 60))

    db = SessionLocal()
    try:
        service = RiskService(db)
        patient_ids = service.get_high_risk_patients(threshold)
        return jsonify({'high_risk_patients': patient_ids})
    finally:
        db.close()