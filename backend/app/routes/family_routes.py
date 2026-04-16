from flask import Blueprint, request, jsonify
from datetime import date
from app.database import SessionLocal
from app.services.family_schedule_service import FamilyScheduleService


family_bp = Blueprint('family', __name__)


@family_bp.route('/families/<family_id>/weekly-summary', methods=['GET'])
def get_family_weekly_summary(family_id):
    """
    Get complete weekly summary for all patients in a family.
    Query parameters:
      - week_start (optional): YYYY-MM-DD format, defaults to Monday of current week
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
        service = FamilyScheduleService(db)
        result = service.get_family_weekly_summary(family_id, week_start)
        status_code = 200 if result.get("success") else 404
        return jsonify(result), status_code
    finally:
        db.close()


@family_bp.route('/patients/<patient_id>/weekly-summary', methods=['GET'])
def get_patient_weekly_summary(patient_id):
    """
    Get complete weekly summary for a single patient.
    Query parameters:
      - week_start (optional): YYYY-MM-DD format, defaults to Monday of current week
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
        service = FamilyScheduleService(db)
        result = service.get_weekly_summary(patient_id, week_start)
        status_code = 200 if result.get("success") else 404
        return jsonify(result), status_code
    finally:
        db.close()
