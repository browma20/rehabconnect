from flask import Blueprint, request, jsonify
from ..services.idt_service import IDTService
from ..database import SessionLocal

idt_bp = Blueprint('idt', __name__)

@idt_bp.route('/patients/<patient_id>/idt-meetings', methods=['POST'])
def create_idt_meeting(patient_id):
    """Create an IDT meeting."""
    data = request.get_json()
    db = SessionLocal()

    try:
        service = IDTService(db)
        meeting = service.create_idt_meeting(
            patient_id=patient_id,
            meeting_datetime=data['meeting_datetime'],
            attendees=data.get('attendees', []),
            notes=data.get('notes')
        )
        return jsonify({
            'meeting_id': meeting.id,
            'patient_id': meeting.patient_id,
            'meeting_datetime': meeting.meeting_datetime.isoformat(),
            'attendees': meeting.attendees,
            'notes': meeting.notes
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@idt_bp.route('/patients/<patient_id>/idt-meetings', methods=['GET'])
def get_idt_meetings(patient_id):
    """Get IDT meetings for a patient."""
    db = SessionLocal()
    try:
        service = IDTService(db)
        meetings = service.get_idt_meetings(patient_id)
        return jsonify([{
            'meeting_id': m.id,
            'meeting_datetime': m.meeting_datetime.isoformat(),
            'attendees': m.attendees,
            'notes': m.notes
        } for m in meetings])
    finally:
        db.close()

@idt_bp.route('/patients/<patient_id>/idt-meetings/<int:meeting_id>', methods=['PUT'])
def update_idt_meeting(patient_id, meeting_id):
    """Update IDT meeting notes."""
    data = request.get_json()
    db = SessionLocal()

    try:
        service = IDTService(db)
        meeting = service.update_meeting_notes(meeting_id, data['notes'])
        return jsonify({
            'meeting_id': meeting.id,
            'notes': meeting.notes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()

@idt_bp.route('/patients/<patient_id>/compliance/idt', methods=['GET'])
def get_idt_compliance(patient_id):
    """Get IDT compliance for a patient."""
    from datetime import date
    target_date = date.today()

    db = SessionLocal()
    try:
        service = IDTService(db)
        compliance = service.get_timeliness_compliance(patient_id, target_date)
        return jsonify(compliance)
    finally:
        db.close()