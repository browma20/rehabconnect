from datetime import date

from flask import Blueprint, jsonify, request

from backend.app.database import SessionLocal
from backend.app.services.predictive_alert_service import PredictiveAlertService


predictive_alert_bp = Blueprint("predictive_alert", __name__)


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_bool(value: str | None):
    if value is None:
        return None

    lowered = value.lower()
    if lowered in {"true", "1", "yes"}:
        return True
    if lowered in {"false", "0", "no"}:
        return False
    return None


@predictive_alert_bp.route("/predictive-alerts", methods=["GET"])
def list_predictive_alerts():
    alert_type = request.args.get("type")
    severity = request.args.get("severity")
    resolved = _parse_bool(request.args.get("resolved"))
    start_date = _parse_date(request.args.get("start_date"))
    end_date = _parse_date(request.args.get("end_date"))

    if request.args.get("resolved") is not None and resolved is None:
        return jsonify({"success": False, "error": "Invalid resolved value; use true/false"}), 400

    if request.args.get("start_date") and start_date is None:
        return jsonify({"success": False, "error": "Invalid start_date format; use YYYY-MM-DD"}), 400

    if request.args.get("end_date") and end_date is None:
        return jsonify({"success": False, "error": "Invalid end_date format; use YYYY-MM-DD"}), 400

    if start_date and end_date and start_date > end_date:
        return jsonify({"success": False, "error": "start_date must be less than or equal to end_date"}), 400

    db = SessionLocal()
    try:
        service = PredictiveAlertService(db)
        alerts = service.list_alerts(
            alert_type=alert_type,
            severity=severity,
            resolved=resolved,
            start_date=start_date,
            end_date=end_date,
        )
        return jsonify({"success": True, "data": alerts}), 200
    finally:
        db.close()


@predictive_alert_bp.route("/predictive-alerts/<int:alert_id>/resolve", methods=["POST"])
def resolve_predictive_alert(alert_id: int):
    db = SessionLocal()
    try:
        service = PredictiveAlertService(db)
        result = service.resolve_alert(alert_id)
        if not result.get("success"):
            return jsonify({"success": False, "error": result.get("error", "Not found")}), 404

        return jsonify(result), 200
    finally:
        db.close()


@predictive_alert_bp.route("/predictive-alerts/run", methods=["POST"])
def run_predictive_alerts():
    data = request.get_json(silent=True) or {}

    start_date_str = data.get("start_date") or request.args.get("start_date")
    end_date_str = data.get("end_date") or request.args.get("end_date")

    if not start_date_str or not end_date_str:
        return jsonify({"success": False, "error": "start_date and end_date are required (YYYY-MM-DD)"}), 400

    start_date = _parse_date(start_date_str)
    end_date = _parse_date(end_date_str)

    if start_date is None or end_date is None:
        return jsonify({"success": False, "error": "Invalid date format; use YYYY-MM-DD"}), 400

    if start_date > end_date:
        return jsonify({"success": False, "error": "start_date must be less than or equal to end_date"}), 400

    db = SessionLocal()
    try:
        service = PredictiveAlertService(db)
        result = service.run_all(start_date, end_date)
        return jsonify({"success": True, "data": result}), 200
    finally:
        db.close()
