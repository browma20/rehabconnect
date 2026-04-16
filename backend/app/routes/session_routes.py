from flask import Blueprint, request, jsonify
from datetime import date, timedelta
from app.database import SessionLocal
from app.services.session_service import SessionService
from app.services.matching_service import MatchingService
from app.services.conflict_detection_service import ConflictDetectionService
from app.services.session_audit_service import SessionAuditService


session_bp = Blueprint('session', __name__)


def _serialize_session(session):
    return {
        "id": session.id,
        "therapist_id": session.therapist_id,
        "patient_id": session.patient_id,
        "date": session.date.isoformat(),
        "start_time": session.start_time.isoformat(),
        "end_time": session.end_time.isoformat(),
        "duration_minutes": int((session.end_time.hour * 60 + session.end_time.minute) - (session.start_time.hour * 60 + session.start_time.minute)),
        "discipline": session.discipline,
        "notes": session.notes,
        "status": session.status,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        "canceled_at": session.canceled_at.isoformat() if session.canceled_at else None,
        "cancellation_reason": session.cancellation_reason,
    }


@session_bp.route('/sessions', methods=['POST'])
def create_session():
    data = request.get_json()
    db = SessionLocal()

    try:
        service = SessionService(db)
        session = service.create_session(data)
        return jsonify(_serialize_session(session)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@session_bp.route('/sessions', methods=['GET'])
def list_sessions():
    db = SessionLocal()
    try:
        service = SessionService(db)
        sessions = service.list_sessions()
        return jsonify([_serialize_session(session) for session in sessions])
    finally:
        db.close()


@session_bp.route('/sessions/open', methods=['GET'])
def list_open_sessions():
    db = SessionLocal()
    try:
        service = SessionService(db)
        sessions = service.list_open_sessions()
        return jsonify([_serialize_session(session) for session in sessions]), 200
    finally:
        db.close()


@session_bp.route('/sessions/auto-assign-all', methods=['POST'])
def auto_assign_all_sessions():
    dry_run = request.args.get('dry_run', 'false').lower() == 'true'
    db = SessionLocal()
    try:
        service = MatchingService(db)
        result = service.bulk_auto_assign(dry_run=dry_run)
        return jsonify(result), 200
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    db = SessionLocal()
    try:
        service = SessionService(db)
        session = service.get_session_by_id(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        return jsonify(_serialize_session(session))
    finally:
        db.close()


@session_bp.route('/sessions/therapist/<therapist_id>', methods=['GET'])
def get_sessions_by_therapist(therapist_id):
    db = SessionLocal()
    try:
        service = SessionService(db)
        sessions = service.get_sessions_by_therapist(therapist_id)
        return jsonify([_serialize_session(session) for session in sessions])
    finally:
        db.close()


@session_bp.route('/sessions/patient/<patient_id>', methods=['GET'])
def get_sessions_by_patient(patient_id):
    db = SessionLocal()
    try:
        service = SessionService(db)
        sessions = service.get_sessions_by_patient(patient_id)
        return jsonify([_serialize_session(session) for session in sessions])
    finally:
        db.close()


@session_bp.route("/patients/<patient_id>/schedule", methods=["GET"])
def get_patient_schedule(patient_id):
    db = SessionLocal()
    service = SessionService(db)
    try:
        schedule = service.get_schedule_for_patient(patient_id)
        return jsonify({
            "patient_id": patient_id,
            "schedule": schedule
        }), 200
    finally:
        db.close()


@session_bp.route('/patients/<patient_id>/schedule/grouped', methods=['GET'])
def get_grouped_patient_schedule(patient_id):
    db = SessionLocal()
    service = SessionService(db)
    try:
        schedule = service.get_grouped_schedule_for_patient(patient_id)
        return jsonify({
            "patient_id": patient_id,
            "schedule": schedule
        }), 200
    finally:
        db.close()


@session_bp.route('/patients/<patient_id>/schedule/today', methods=['GET'])
def get_todays_schedule(patient_id):
    db = SessionLocal()
    service = SessionService(db)
    try:
        schedule = service.get_todays_schedule_for_patient(patient_id)
        return jsonify({
            "patient_id": patient_id,
            "schedule": schedule
        }), 200
    finally:
        db.close()


@session_bp.route('/therapists/<therapist_id>/schedule/today', methods=['GET'])
def get_todays_schedule_for_therapist(therapist_id):
    db = SessionLocal()
    service = SessionService(db)
    try:
        schedule = service.get_todays_schedule_for_therapist(therapist_id)
        return jsonify({
            "therapist_id": therapist_id,
            "schedule": schedule
        }), 200
    finally:
        db.close()


@session_bp.route('/therapists/<therapist_id>/schedule/week', methods=['GET'])
def get_weekly_schedule_for_therapist(therapist_id):
    db = SessionLocal()
    service = SessionService(db)
    try:
        schedule = service.get_weekly_schedule_for_therapist(therapist_id)
        return jsonify({
            "therapist_id": therapist_id,
            "schedule": schedule
        }), 200
    finally:
        db.close()


@session_bp.route('/therapists/<therapist_id>/schedule/grouped', methods=['GET'])
def get_grouped_schedule_for_therapist(therapist_id):
    db = SessionLocal()
    service = SessionService(db)
    try:
        schedule = service.get_grouped_schedule_for_therapist(therapist_id)
        return jsonify({
            "therapist_id": therapist_id,
            "schedule": schedule
        }), 200
    finally:
        db.close()


@session_bp.route('/therapists/<therapist_id>/next-session', methods=['GET'])
def get_next_session_for_therapist(therapist_id):
    db = SessionLocal()
    service = SessionService(db)
    try:
        next_session = service.get_next_session_for_therapist(therapist_id)
        return jsonify({
            "therapist_id": therapist_id,
            "next_session": next_session
        }), 200
    finally:
        db.close()


@session_bp.route('/therapists/<therapist_id>/schedule/summary', methods=['GET'])
def get_weekly_summary_for_therapist(therapist_id):
    db = SessionLocal()
    service = SessionService(db)
    try:
        days = request.args.get('days', 7, type=int)
        summary = service.get_weekly_summary_for_therapist(therapist_id, days=days)
        week_start = date.today()
        week_end = week_start + timedelta(days=days)
        return jsonify({
            "therapist_id": therapist_id,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "summary": summary
        }), 200
    finally:
        db.close()


@session_bp.route('/patients/<patient_id>/next-session', methods=['GET'])
def get_next_session(patient_id):
    db = SessionLocal()
    service = SessionService(db)
    try:
        next_session = service.get_next_session_for_patient(patient_id)
        return jsonify({
            "patient_id": patient_id,
            "next_session": next_session
        }), 200
    finally:
        db.close()

@session_bp.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    db = SessionLocal()
    try:
        service = SessionService(db)
        success = service.delete_session(session_id)
        if not success:
            return jsonify({"error": "Session not found"}), 404

        return jsonify({"message": "Session deleted"})
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>/match', methods=['POST'])
def match_therapists(session_id):
    db = SessionLocal()
    try:
        service = MatchingService(db)
        result = service.match_therapists_to_session(session_id)
        if result is None:
            return jsonify({"error": "Session not found"}), 404
        return jsonify({
            "session_id": session_id,
            "best_match": result["best_match"],
            "alternatives": result["alternatives"],
        }), 200
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>/conflicts', methods=['GET'])
def detect_conflicts(session_id):
    db = SessionLocal()
    try:
        service = ConflictDetectionService(db)
        result = service.detect_conflicts_for_session(session_id)
        if result is None:
            return jsonify({"error": "Session not found"}), 404
        return jsonify(result), 200
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>/pickup', methods=['POST'])
def pickup_session(session_id):
    data = request.get_json()
    db = SessionLocal()
    try:
        service = SessionService(db)
        therapist_id = data.get("therapist_id") if data else None
        if not therapist_id:
            return jsonify({"error": "therapist_id is required"}), 400
        result = service.request_shift_pickup(session_id, therapist_id)
        if result is None:
            return jsonify({"error": "Session not found"}), 404
        status_code = 200 if result["success"] else 409
        return jsonify(result), status_code
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    data = request.get_json() or {}
    db = SessionLocal()
    try:
        service = SessionService(db)
        result = service.complete_session(session_id, notes=data.get("notes"))
        if result is None:
            return jsonify({"error": "Session not found"}), 404
        return jsonify(result), 200
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>/cancel', methods=['POST'])
def cancel_session(session_id):
    data = request.get_json() or {}
    db = SessionLocal()
    try:
        service = SessionService(db)
        result = service.cancel_session(session_id, reason=data.get("reason"))
        if result is None:
            return jsonify({"error": "Session not found"}), 404
        return jsonify(result), 200
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>/auto-assign', methods=['POST'])
def auto_assign_session(session_id):
    db = SessionLocal()
    try:
        service = MatchingService(db)
        result = service.auto_assign_session(session_id)
        if result is None:
            return jsonify({"error": "Session not found"}), 404
        status_code = 200 if result["success"] else 409
        return jsonify(result), status_code
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>/reschedule', methods=['POST'])
def reschedule_session(session_id):
    data = request.get_json() or {}
    db = SessionLocal()
    try:
        service = SessionService(db)
        result = service.reschedule_session(
            session_id,
            data.get("date"),
            data.get("start_time"),
            data.get("end_time"),
        )
        if result is None:
            return jsonify({"error": "Session not found"}), 404
        if result.get("success"):
            return jsonify(result), 200
        status_code = 409 if result.get("conflicts") else 400
        return jsonify(result), status_code
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>/smart-reschedule', methods=['POST'])
def smart_reschedule_session(session_id):
    db = SessionLocal()
    try:
        service = MatchingService(db)
        result = service.smart_reschedule_session(session_id)
        if result is None:
            return jsonify({"error": "Session not found"}), 404
        status_code = 200 if result["success"] else 409
        return jsonify(result), status_code
    finally:
        db.close()


@session_bp.route('/sessions/<session_id>/audit-log', methods=['GET'])
def get_session_audit_log(session_id):
    db = SessionLocal()
    try:
        service = SessionService(db)
        session = service.get_session_by_id(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        audit_service = SessionAuditService(db)
        audit_log = audit_service.get_audit_log(session_id)
        return jsonify({
            "session_id": session_id,
            "audit_log": audit_log,
        }), 200
    finally:
        db.close()