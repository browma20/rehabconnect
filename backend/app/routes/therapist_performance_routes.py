from flask import Blueprint, request, jsonify

from app.database import SessionLocal
from app.services.therapist_performance_service import TherapistPerformanceService

therapist_performance_bp = Blueprint("therapist_performance", __name__)

_DEFAULT_WEEKS = 12
_MAX_WEEKS = 52


def _parse_weeks() -> tuple[int | None, str | None]:
    """Parse ?weeks= query param. Returns (value, error_message)."""
    raw = request.args.get("weeks")
    if raw is None:
        return _DEFAULT_WEEKS, None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None, "weeks must be an integer"
    if not (1 <= value <= _MAX_WEEKS):
        return None, f"weeks must be between 1 and {_MAX_WEEKS}"
    return value, None


# ---------------------------------------------------------------------------
# GET /api/therapists/<id>/performance
# ---------------------------------------------------------------------------
@therapist_performance_bp.route("/therapists/<therapist_id>/performance", methods=["GET"])
def get_therapist_performance(therapist_id: str):
    """
    Return the full performance profile for a single therapist.

    Query params:
      weeks  (int, 1–52, default 12) – lookback window
    """
    weeks, err = _parse_weeks()
    if err:
        return jsonify({"success": False, "error": err}), 400

    db = SessionLocal()
    try:
        svc = TherapistPerformanceService(db)
        result = svc.get_performance_profile(therapist_id=therapist_id, weeks=weeks)
        if not result.get("success"):
            status = 404 if "not found" in result.get("error", "").lower() else 400
            return jsonify(result), status
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /api/therapists/performance/overview
# ---------------------------------------------------------------------------
@therapist_performance_bp.route("/therapists/performance/overview", methods=["GET"])
def get_all_therapists_performance():
    """
    Return performance profiles for all therapists, sorted by
    performance_score descending.

    Query params:
      weeks  (int, 1–52, default 12) – lookback window
    """
    weeks, err = _parse_weeks()
    if err:
        return jsonify({"success": False, "error": err}), 400

    db = SessionLocal()
    try:
        svc = TherapistPerformanceService(db)
        result = svc.get_all_therapists_performance(weeks=weeks)
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()
