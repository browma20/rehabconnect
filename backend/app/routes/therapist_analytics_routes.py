from datetime import date, timedelta

from flask import Blueprint, jsonify, request

from app.database import SessionLocal
from app.services.therapist_analytics_service import TherapistAnalyticsService


therapist_analytics_bp = Blueprint("therapist_analytics", __name__)


def _default_week_range() -> tuple[date, date]:
    today = date.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    return start, end


def _parse_date_range() -> tuple[date, date, str | None]:
    default_start, default_end = _default_week_range()

    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    try:
        start_date = date.fromisoformat(start_date_str) if start_date_str else default_start
        end_date = date.fromisoformat(end_date_str) if end_date_str else default_end
    except ValueError:
        return default_start, default_end, "Invalid date format; use YYYY-MM-DD"

    if start_date > end_date:
        return default_start, default_end, "start_date must be less than or equal to end_date"

    return start_date, end_date, None


@therapist_analytics_bp.route("/therapists/<therapist_id>/productivity", methods=["GET"])
def get_therapist_productivity(therapist_id: str):
    start_date, end_date, error = _parse_date_range()
    if error:
        return jsonify({"success": False, "error": error}), 400

    db = SessionLocal()
    try:
        service = TherapistAnalyticsService(db)
        result = service.get_productivity(therapist_id, start_date, end_date)

        if not result.get("success"):
            return jsonify({"success": False, "error": result.get("error", "Not found")}), 404

        return jsonify({"success": True, "data": result}), 200
    finally:
        db.close()


@therapist_analytics_bp.route("/therapists/productivity/overview", methods=["GET"])
def get_therapists_productivity_overview():
    start_date, end_date, error = _parse_date_range()
    if error:
        return jsonify({"success": False, "error": error}), 400

    db = SessionLocal()
    try:
        service = TherapistAnalyticsService(db)
        result = service.get_all_therapists_productivity(start_date, end_date)
        return jsonify({"success": True, "data": result}), 200
    finally:
        db.close()
