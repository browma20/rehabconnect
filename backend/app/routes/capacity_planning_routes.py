from flask import Blueprint, jsonify, request

from app.database import SessionLocal
from app.services.capacity_planning_service import CapacityPlanningService


capacity_planning_bp = Blueprint("capacity_planning", __name__)


def _parse_weeks() -> tuple[int, str | None]:
    weeks_str = request.args.get("weeks", "12")
    try:
        weeks = int(weeks_str)
        if weeks < 1 or weeks > 52:
            raise ValueError
        return weeks, None
    except ValueError:
        return 12, "weeks must be an integer between 1 and 52"


@capacity_planning_bp.route("/capacity-planning", methods=["GET"])
def forecast_all_disciplines():
    weeks, error = _parse_weeks()
    if error:
        return jsonify({"success": False, "error": error}), 400

    db = SessionLocal()
    try:
        service = CapacityPlanningService(db)
        result = service.forecast_all_disciplines(weeks)
        return jsonify({"success": True, "data": result}), 200
    finally:
        db.close()


# NOTE: This route is registered before /<discipline> so that
# GET /capacity-planning/therapists/<id> is never captured by the
# discipline parameter. Werkzeug also gives precedence to literal URL
# segments over parametric ones, but explicit ordering makes it clear.
@capacity_planning_bp.route(
    "/capacity-planning/therapists/<therapist_id>", methods=["GET"]
)
def forecast_therapist(therapist_id: str):
    weeks, error = _parse_weeks()
    if error:
        return jsonify({"success": False, "error": error}), 400

    db = SessionLocal()
    try:
        service = CapacityPlanningService(db)
        result = service.forecast_therapist(therapist_id, weeks)
        if not result.get("success"):
            return (
                jsonify({"success": False, "error": result.get("error", "Not found")}),
                404,
            )
        return jsonify({"success": True, "data": result}), 200
    finally:
        db.close()


@capacity_planning_bp.route("/capacity-planning/<discipline>", methods=["GET"])
def forecast_discipline(discipline: str):
    weeks, error = _parse_weeks()
    if error:
        return jsonify({"success": False, "error": error}), 400

    db = SessionLocal()
    try:
        service = CapacityPlanningService(db)
        result = service.forecast_discipline(discipline.upper(), weeks)
        return jsonify({"success": True, "data": result}), 200
    finally:
        db.close()
