from flask import Blueprint, request, jsonify
from ..services.physician_evaluation_service import PhysicianEvaluationService
from ..database import SessionLocal

physician_bp = Blueprint('physician', __name__)

@physician_bp.route('/patients/<patient_id>/physician-evaluations', methods=['POST'])
def create_physician_evaluation(patient_id):
    """Create a physician evaluation."""
    data = request.get_json()
    db = SessionLocal()

    try:
        service = PhysicianEvaluationService(db)
        evaluation = service.create_physician_evaluation(
            patient_id=patient_id,
            physician_id=data['physician_id'],
            evaluation_datetime=data.get('evaluation_datetime'),
            notes=data.get('notes')
        )
        return jsonify({
            'evaluation_id': evaluation.id,
            'patient_id': evaluation.patient_id,
            'physician_id': evaluation.physician_id,
            'evaluation_datetime': evaluation.evaluation_datetime.isoformat(),
            'notes': evaluation.notes
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@physician_bp.route('/patients/<patient_id>/physician-evaluations', methods=['GET'])
def get_physician_evaluations(patient_id):
    """Get physician evaluations for a patient."""
    db = SessionLocal()
    try:
        service = PhysicianEvaluationService(db)
        evaluations = service.get_physician_evaluations(patient_id)
        return jsonify([{
            'evaluation_id': e.id,
            'physician_id': e.physician_id,
            'evaluation_datetime': e.evaluation_datetime.isoformat(),
            'notes': e.notes
        } for e in evaluations])
    finally:
        db.close()

@physician_bp.route('/patients/<patient_id>/compliance/first-day', methods=['GET'])
def get_first_day_compliance(patient_id):
    """Get first-day compliance for a patient."""
    db = SessionLocal()
    try:
        service = PhysicianEvaluationService(db)
        compliance = service.get_first_day_compliance(patient_id)
        return jsonify(compliance)
    finally:
        db.close()