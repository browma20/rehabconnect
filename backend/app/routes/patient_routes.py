import logging

from flask import Blueprint, request, jsonify
from ..services.patient_service import PatientService
from ..database import SessionLocal

patient_bp = Blueprint('patient', __name__)
logger = logging.getLogger(__name__)

@patient_bp.route('/patients', methods=['POST'])
def create_patient():
    """Create a new patient."""
    data = request.get_json()
    db = SessionLocal()
    try:
        service = PatientService(db)
        patient = service.create_patient(data)
        return jsonify({
            'patient_id': patient.patient_id,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'admission_datetime': patient.admission_datetime.isoformat()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@patient_bp.route('/patients/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get patient details."""
    db = SessionLocal()

    try:
        service = PatientService(db)
        patient = service.get_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404

        return jsonify({
            'patient_id': patient.patient_id,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'admission_datetime': patient.admission_datetime.isoformat(),
            'discharge_datetime': patient.discharge_datetime.isoformat() if patient.discharge_datetime else None
        })
    finally:
        db.close()

@patient_bp.route('/patients/<patient_id>', methods=['PUT'])
def update_patient(patient_id):
    """Update patient information."""
    data = request.get_json() or {}
    db = SessionLocal()
    try:
        service = PatientService(db)
        patient = service.update_patient(patient_id, **data)
        return jsonify({
            'patient_id': patient.patient_id,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'admission_datetime': patient.admission_datetime.isoformat(),
            'discharge_datetime': patient.discharge_datetime.isoformat() if patient.discharge_datetime else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@patient_bp.route('/patients/<patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    """Delete a patient."""
    db = SessionLocal()

    try:
        service = PatientService(db)
        service.delete_patient(patient_id)
        return jsonify({'message': 'Patient deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@patient_bp.route('/patients', methods=['GET'])
def list_patients():
    """List all patients."""
    db = SessionLocal()
    try:
        service = PatientService(db)
        patients = service.list_patients()
        return jsonify([{
            'patient_id': p.patient_id,
            'first_name': p.first_name,
            'last_name': p.last_name,
            'admission_datetime': p.admission_datetime.isoformat(),
            'discharge_datetime': p.discharge_datetime.isoformat() if p.discharge_datetime else None
        } for p in patients])
    except Exception as e:
        logger.exception("Failed to list patients")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()
