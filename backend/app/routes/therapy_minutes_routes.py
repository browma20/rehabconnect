from flask import Blueprint, request, jsonify
from datetime import date
from ..services.therapy_minutes_service import TherapyMinutesService
from ..database import SessionLocal

therapy_bp = Blueprint('therapy', __name__)

@therapy_bp.route('/patients/<patient_id>/therapy-sessions', methods=['POST'])
def add_therapy_session(patient_id):
    """Add a new therapy session."""
    data = request.get_json()
    db = SessionLocal()

    try:
        service = TherapyMinutesService(db)
        session = service.add_therapy_session(
            patient_id=patient_id,
            therapy_type=data['therapy_type'],
            minutes=data['minutes'],
            therapist_id=data['therapist_id'],
            timestamp=data.get('timestamp')
        )
        return jsonify({
            'session_id': session.id,
            'patient_id': session.patient_id,
            'therapy_type': session.therapy_type,
            'minutes': session.minutes,
            'therapist_id': session.therapist_id,
            'timestamp': session.timestamp.isoformat()
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@therapy_bp.route('/patients/<patient_id>/therapy-sessions', methods=['GET'])
def get_therapy_sessions(patient_id):
    """Get therapy sessions for a patient."""
    db = SessionLocal()
    try:
        service = TherapyMinutesService(db)
        sessions = service.get_therapy_sessions(patient_id)
        return jsonify([{
            'session_id': s.id,
            'therapy_type': s.therapy_type,
            'minutes': s.minutes,
            'therapist_id': s.therapist_id,
            'timestamp': s.timestamp.isoformat()
        } for s in sessions])
    finally:
        db.close()

@therapy_bp.route('/patients/<patient_id>/compliance/daily', methods=['GET'])
def get_daily_compliance(patient_id):
    """Get daily compliance for a patient."""
    date_str = request.args.get('date')
    if not date_str:
        target_date = date.today()
    else:
        target_date = date.fromisoformat(date_str)

    db = SessionLocal()
    try:
        service = TherapyMinutesService(db)
        compliance = service.get_daily_compliance(patient_id, target_date)
        return jsonify(compliance)
    finally:
        db.close()

@therapy_bp.route('/patients/<patient_id>/compliance/rolling', methods=['GET'])
def get_rolling_compliance(patient_id):
    """Get rolling compliance for a patient."""
    db = SessionLocal()
    try:
        service = TherapyMinutesService(db)
        compliance = service.get_rolling_compliance(patient_id)
        return jsonify(compliance)
    finally:
        db.close()

@therapy_bp.route('/patients/<patient_id>/therapy-summary', methods=['GET'])
def get_therapy_summary(patient_id):
    """Get therapy summary for a patient."""
    db = SessionLocal()
    try:
        service = TherapyMinutesService(db)
        summary = service.get_therapy_summary(patient_id)
        return jsonify(summary)
    finally:
        db.close()