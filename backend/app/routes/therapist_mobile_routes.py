from flask import Blueprint, request, jsonify
from datetime import date
from app.database import SessionLocal
from app.services.therapist_mobile_service import TherapistMobileService


therapist_mobile_bp = Blueprint('therapist_mobile', __name__)


@therapist_mobile_bp.route('/therapists/<therapist_id>/schedule/today', methods=['GET'])
def get_daily_schedule(therapist_id):
    """
    Get therapist's schedule for today.
    Query parameters:
      - date (optional): YYYY-MM-DD format, defaults to today
    """
    date_str = request.args.get('date')
    date_value = None

    if date_str:
        try:
            date_value = date.fromisoformat(date_str)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format; use YYYY-MM-DD"}), 400

    db = SessionLocal()
    try:
        service = TherapistMobileService(db)
        result = service.get_daily_schedule(therapist_id, date_value)
        status_code = 200 if result.get("success") else 404
        return jsonify(result), status_code
    finally:
        db.close()


@therapist_mobile_bp.route('/therapists/<therapist_id>/schedule/week', methods=['GET'])
def get_weekly_schedule(therapist_id):
    """
    Get therapist's schedule for a full week.
    Query parameters:
      - week_start (optional): YYYY-MM-DD format, defaults to current week
    """
    week_start_str = request.args.get('week_start')
    week_start = None

    if week_start_str:
        try:
            week_start = date.fromisoformat(week_start_str)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format; use YYYY-MM-DD"}), 400

    db = SessionLocal()
    try:
        service = TherapistMobileService(db)
        result = service.get_weekly_schedule(therapist_id, week_start)
        status_code = 200 if result.get("success") else 404
        return jsonify(result), status_code
    finally:
        db.close()


@therapist_mobile_bp.route('/therapists/<therapist_id>/sessions/<session_id>/complete', methods=['POST'])
def complete_session(therapist_id, session_id):
    """
    Mark a session as completed.
    JSON body (optional):
      {
        "notes": "Session notes here"
      }
    """
    data = request.get_json() or {}
    notes = data.get('notes')

    db = SessionLocal()
    try:
        service = TherapistMobileService(db)
        result = service.complete_session(therapist_id, session_id, notes=notes)
        status_code = 200 if result.get("success") else 400
        return jsonify(result), status_code
    finally:
        db.close()


@therapist_mobile_bp.route('/therapists/<therapist_id>/sessions/<session_id>/cancel', methods=['POST'])
def cancel_session(therapist_id, session_id):
    """
    Cancel a session.
    JSON body (optional):
      {
        "reason": "Cancellation reason here"
      }
    """
    data = request.get_json() or {}
    reason = data.get('reason')

    db = SessionLocal()
    try:
        service = TherapistMobileService(db)
        result = service.cancel_session(therapist_id, session_id, reason=reason)
        status_code = 200 if result.get("success") else 400
        return jsonify(result), status_code
    finally:
        db.close()


@therapist_mobile_bp.route('/therapists/<therapist_id>/sessions/<session_id>/reschedule', methods=['POST'])
def reschedule_session(therapist_id, session_id):
    """
    Reschedule a session.
    JSON body (required):
      {
        "date": "YYYY-MM-DD",
        "start_time": "HH:MM:SS",
        "end_time": "HH:MM:SS"
      }
    """
    data = request.get_json() or {}
    date_value = data.get('date')
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if not date_value or not start_time or not end_time:
        return jsonify({"success": False, "error": "date, start_time, and end_time are required"}), 400

    db = SessionLocal()
    try:
        service = TherapistMobileService(db)
        result = service.reschedule_session(therapist_id, session_id, date_value, start_time, end_time)
        status_code = 200 if result.get("success") else 400
        return jsonify(result), status_code
    finally:
        db.close()


@therapist_mobile_bp.route('/therapists/<therapist_id>/open-sessions', methods=['GET'])
def list_open_sessions(therapist_id):
    """
    Get list of open sessions matching therapist's discipline.
    """
    db = SessionLocal()
    try:
        service = TherapistMobileService(db)
        result = service.list_open_sessions(therapist_id)
        status_code = 200 if result.get("success") else 404
        return jsonify(result), status_code
    finally:
        db.close()


@therapist_mobile_bp.route('/therapists/<therapist_id>/sessions/<session_id>/pickup', methods=['POST'])
def pickup_session(therapist_id, session_id):
    """
    Therapist picks up an open session (shift pickup).
    """
    db = SessionLocal()
    try:
        service = TherapistMobileService(db)
        result = service.pickup_session(therapist_id, session_id)
        status_code = 200 if result.get("success") else 400
        return jsonify(result), status_code
    finally:
        db.close()


@therapist_mobile_bp.route('/therapists/<therapist_id>/notifications', methods=['GET'])
def get_notifications(therapist_id):
    """
    Get therapist's notifications.
    Query parameters:
      - unread_only (optional, default=false): if true, only return unread notifications
    """
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    db = SessionLocal()
    try:
        service = TherapistMobileService(db)
        result = service.get_notifications(therapist_id, unread_only=unread_only)
        status_code = 200 if result.get("success") else 404
        return jsonify(result), status_code
    finally:
        db.close()
