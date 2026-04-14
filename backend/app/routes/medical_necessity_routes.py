from flask import Blueprint, request, jsonify
from ..services.medical_necessity_service import MedicalNecessityService
from ..database import SessionLocal

medical_bp = Blueprint('medical', __name__)

@medical_bp.route('/patients/<patient_id>/medical-necessity-records', methods=['POST'])
def add_medical_necessity_record(patient_id):
    """Add a medical necessity record."""
    data = request.get_json()
    db = SessionLocal()

    try:
        service = MedicalNecessityService(db)
        record = service.add_medical_necessity_record(
            patient_id=patient_id,
            justification=data['justification'],
            clinician_id=data['clinician_id'],
            assessment_date=data.get('assessment_date')
        )
        return jsonify({
            'record_id': record.id,
            'patient_id': record.patient_id,
            'justification': record.justification,
            'clinician_id': record.clinician_id,
            'assessment_date': record.assessment_date.isoformat()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@medical_bp.route('/patients/<patient_id>/medical-necessity-records', methods=['GET'])
def get_medical_necessity_records(patient_id):
    """Get medical necessity records for a patient."""
    db = SessionLocal()
    try:
        service = MedicalNecessityService(db)
        records = service.get_medical_necessity_records(patient_id)
        return jsonify([{
            'record_id': r.id,
            'justification': r.justification,
            'clinician_id': r.clinician_id,
            'assessment_date': r.assessment_date.isoformat()
        } for r in records])
    finally:
        db.close()

@medical_bp.route('/patients/<patient_id>/compliance/medical-necessity', methods=['GET'])
def get_medical_necessity_compliance(patient_id):
    """Get medical necessity compliance for a patient."""
    db = SessionLocal()
    try:
        service = MedicalNecessityService(db)
        compliance = service.get_collection_compliance(patient_id)
        return jsonify(compliance)
    finally:
        db.close()