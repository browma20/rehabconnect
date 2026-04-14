from flask import Blueprint, request, jsonify, send_file
import os
from ..services.integration_service import IntegrationService
from ..database import SessionLocal

integration_bp = Blueprint('integration', __name__)

@integration_bp.route('/patients/<patient_id>/export/csv', methods=['GET'])
def export_patient_csv(patient_id):
    """Export patient data as CSV."""
    filepath = f"temp_{patient_id}.csv"
    db = SessionLocal()
    try:
        service = IntegrationService(db)
        success = service.export_patient_data_csv(patient_id, filepath)
        if not success:
            return jsonify({'error': 'Export failed'}), 400

        return send_file(filepath, as_attachment=True, download_name=f"{patient_id}_data.csv")
    finally:
        db.close()
        if os.path.exists(filepath):
            os.remove(filepath)

@integration_bp.route('/patients/<patient_id>/export/fhir', methods=['GET'])
def export_patient_fhir(patient_id):
    """Export patient data as FHIR Bundle."""
    db = SessionLocal()
    try:
        service = IntegrationService(db)
        bundle = service.export_fhir_bundle(patient_id)
        if not bundle:
            return jsonify({'error': 'Export failed'}), 400

        return jsonify(bundle)
    finally:
        db.close()

@integration_bp.route('/patients/<patient_id>/export/hl7', methods=['GET'])
def export_patient_hl7(patient_id):
    """Export patient data as HL7 message."""
    db = SessionLocal()
    try:
        service = IntegrationService(db)
        message = service.export_hl7_message(patient_id)
        if not message:
            return jsonify({'error': 'Export failed'}), 400

        return jsonify({'hl7_message': message})
    finally:
        db.close()

@integration_bp.route('/import/csv', methods=['POST'])
def import_csv():
    """Import data from CSV file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filepath = f"temp_import_{file.filename}"
    file.save(filepath)

    db = SessionLocal()
    try:
        service = IntegrationService(db)
        success = service.import_patient_data_csv(filepath)
        if success:
            return jsonify({'message': 'Import successful'}), 200
        else:
            return jsonify({'error': 'Import failed'}), 400
    finally:
        db.close()
        if os.path.exists(filepath):
            os.remove(filepath)

@integration_bp.route('/import/fhir', methods=['POST'])
def import_fhir():
    """Import data from FHIR Bundle."""
    data = request.get_json()
    db = SessionLocal()
    try:
        service = IntegrationService(db)
        success = service.import_fhir_bundle(data)
        if success:
            return jsonify({'message': 'Import successful'}), 200
        else:
            return jsonify({'error': 'Import failed'}), 400
    finally:
        db.close()

@integration_bp.route('/import/hl7', methods=['POST'])
def import_hl7():
    """Import data from HL7 message."""
    data = request.get_json()
    hl7_message = data.get('hl7_message', '')

    db = SessionLocal()
    try:
        service = IntegrationService(db)
        success = service.import_hl7_message(hl7_message)
        if success:
            return jsonify({'message': 'Import successful'}), 200
        else:
            return jsonify({'error': 'Import failed'}), 400
    finally:
        db.close()