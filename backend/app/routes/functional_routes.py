from flask import Blueprint, request, jsonify
from ..services.functional_service import FunctionalService
from ..database import SessionLocal

functional_bp = Blueprint('functional', __name__)

@functional_bp.route('/patients/<patient_id>/functional-scores', methods=['POST'])
def add_functional_score(patient_id):
    """Add a functional score."""
    data = request.get_json()
    db = SessionLocal()

    try:
        service = FunctionalService(db)
        score = service.add_functional_score(
            patient_id=patient_id,
            score_type=data['score_type'],
            score_value=data['score_value'],
            assessor_id=data['assessor_id'],
            assessment_date=data.get('assessment_date')
        )
        return jsonify({
            'score_id': score.id,
            'patient_id': score.patient_id,
            'score_type': score.score_type,
            'score_value': score.score_value,
            'assessor_id': score.assessor_id,
            'assessment_date': score.assessment_date.isoformat()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@functional_bp.route('/patients/<patient_id>/functional-scores', methods=['GET'])
def get_functional_scores(patient_id):
    """Get functional scores for a patient."""
    db = SessionLocal()
    try:
        service = FunctionalService(db)
        scores = service.get_functional_scores(patient_id)
        return jsonify([{
            'score_id': s.id,
            'score_type': s.score_type,
            'score_value': s.score_value,
            'assessor_id': s.assessor_id,
            'assessment_date': s.assessment_date.isoformat()
        } for s in scores])
    finally:
        db.close()

@functional_bp.route('/patients/<patient_id>/functional-summary', methods=['GET'])
def get_functional_summary(patient_id):
    """Get functional summary for a patient."""
    db = SessionLocal()
    try:
        service = FunctionalService(db)
        summary = service.get_functional_summary(patient_id)
        return jsonify(summary)
    finally:
        db.close()

@functional_bp.route('/patients/<patient_id>/compliance/functional', methods=['GET'])
def get_functional_compliance(patient_id):
    """Get functional improvement compliance for a patient."""
    db = SessionLocal()
    try:
        service = FunctionalService(db)
        compliance = service.get_functional_compliance(patient_id)
        return jsonify(compliance)
    finally:
        db.close()