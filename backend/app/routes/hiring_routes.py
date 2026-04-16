from flask import Blueprint, request, jsonify

from app.database import SessionLocal
from app.services.hiring_recommendation_service import HiringRecommendationService

hiring_bp = Blueprint("hiring", __name__)

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
# GET /api/hiring/recommendations
# ---------------------------------------------------------------------------
@hiring_bp.route("/hiring/recommendations", methods=["GET"])
def get_all_recommendations():
    """
    Return hiring recommendations for all disciplines, sorted by
    priority (highest FTE need first).

    Query params:
      weeks  (int, 1–52, default 12) – forecasting window
    """
    weeks, err = _parse_weeks()
    if err:
        return jsonify({"success": False, "error": err}), 400

    db = SessionLocal()
    try:
        svc = HiringRecommendationService(db)
        result = svc.generate_recommendations(weeks=weeks)
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /api/hiring/recommendations/<discipline>
# ---------------------------------------------------------------------------
@hiring_bp.route("/hiring/recommendations/<discipline>", methods=["GET"])
def get_discipline_recommendation(discipline: str):
    """
    Return hiring recommendation for a single discipline.

    Query params:
      weeks  (int, 1–52, default 12) – forecasting window
    """
    weeks, err = _parse_weeks()
    if err:
        return jsonify({"success": False, "error": err}), 400

    discipline = discipline.upper()
    if discipline not in ("PT", "OT", "ST"):
        return (
            jsonify(
                {
                    "success": False,
                    "error": "discipline must be one of: PT, OT, ST",
                }
            ),
            400,
        )

    db = SessionLocal()
    try:
        svc = HiringRecommendationService(db)
        result = svc.generate_recommendation_for_discipline(
            discipline=discipline, weeks=weeks
        )
        if not result.get("success"):
            return jsonify(result), 400
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()
