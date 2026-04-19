from flask import Blueprint, request, jsonify

from app.database import SessionLocal
from app.models import Session as SessionModel
from app.services.marketplace_service import MarketplaceService, AUTO_ASSIGN_THRESHOLD

marketplace_bp = Blueprint("marketplace", __name__)


# ---------------------------------------------------------------------------
# GET /api/marketplace - List all marketplace items (pending session requests)
# ---------------------------------------------------------------------------
@marketplace_bp.route("/", methods=["GET"])
def list_marketplace():
    """Get list of all pending session requests."""
    db = SessionLocal()
    try:
        # Query all pending sessions (unassigned: no therapist_id)
        pending_sessions = db.query(SessionModel).filter(
            SessionModel.status == "scheduled",
            SessionModel.therapist_id.is_(None)
        ).all()
        
        result = [
            {
                "id": s.id,
                "patient_id": s.patient_id,
                "date": s.date.isoformat() if s.date else None,
                "start_time": str(s.start_time) if s.start_time else None,
                "end_time": str(s.end_time) if s.end_time else None,
                "discipline": s.discipline,
                "status": s.status,
                "notes": s.notes
            }
            for s in pending_sessions
        ]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# POST /api/marketplace/request-session
# ---------------------------------------------------------------------------
@marketplace_bp.route("/request-session", methods=["POST"])
def request_session():
    """
    Create a pending (unassigned) session request.

    Body (JSON):
      {
        "patient_id":       "...",
        "discipline":       "OT" | "PT" | "ST",
        "preferred_times":  [
          {"date": "YYYY-MM-DD", "start_time": "HH:MM:SS", "end_time": "HH:MM:SS"},
          ...
        ],
        "duration":    <int, minutes, optional>,
        "recurrence":  "<string, optional – e.g. 'weekly'>"
      }
    """
    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id", "").strip()
    discipline = data.get("discipline", "").strip()
    preferred_times = data.get("preferred_times", [])
    duration = data.get("duration")
    recurrence = data.get("recurrence")

    if not patient_id:
        return jsonify({"success": False, "error": "patient_id is required"}), 400
    if not discipline:
        return jsonify({"success": False, "error": "discipline is required"}), 400
    if not isinstance(preferred_times, list) or not preferred_times:
        return jsonify({"success": False, "error": "preferred_times must be a non-empty list"}), 400

    db = SessionLocal()
    try:
        svc = MarketplaceService(db)
        result = svc.request_session(
            patient_id=patient_id,
            discipline=discipline,
            preferred_times=preferred_times,
            duration=duration,
            recurrence=recurrence,
        )
        if not result.get("success"):
            status = 404 if "not found" in result.get("error", "").lower() else 400
            return jsonify(result), status
        return jsonify({"success": True, "data": result}), 201
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# POST /api/marketplace/assign
# ---------------------------------------------------------------------------
@marketplace_bp.route("/assign", methods=["POST"])
def auto_assign():
    """
    Attempt to auto-assign the best-scoring therapist to a session.

    Body (JSON):
      {
        "session_id": "...",
        "threshold":  <float, optional – defaults to AUTO_ASSIGN_THRESHOLD>
      }

    Returns:
      auto_assigned=True  → therapist was assigned
      auto_assigned=False → ranked list returned for manual review
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "").strip()
    if not session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400

    raw_threshold = data.get("threshold")
    try:
        threshold = float(raw_threshold) if raw_threshold is not None else AUTO_ASSIGN_THRESHOLD
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "threshold must be a number"}), 400
    if not (0 <= threshold <= 100):
        return jsonify({"success": False, "error": "threshold must be between 0 and 100"}), 400

    db = SessionLocal()
    try:
        svc = MarketplaceService(db)
        result = svc.auto_assign_best(session_id=session_id, threshold=threshold)
        if not result.get("success") and "error" in result:
            status = 404 if "not found" in result.get("error", "").lower() else 400
            return jsonify(result), status
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# GET /api/marketplace/recommendations
# ---------------------------------------------------------------------------
@marketplace_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    """
    Return the scored and ranked therapist list for a session.

    Query params:
      session_id  (required)
    """
    session_id = request.args.get("session_id", "").strip()
    if not session_id:
        return jsonify({"success": False, "error": "session_id query param is required"}), 400

    db = SessionLocal()
    try:
        svc = MarketplaceService(db)
        result = svc.score_therapists(session_id=session_id)
        if not result.get("success"):
            status = 404 if "not found" in result.get("error", "").lower() else 400
            return jsonify(result), status
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# POST /api/marketplace/confirm-assignment
# ---------------------------------------------------------------------------
@marketplace_bp.route("/confirm-assignment", methods=["POST"])
def confirm_assignment():
    """
    Scheduler manually confirms a therapist assignment from the ranked list.

    Body (JSON):
      {
        "session_id":    "...",
        "therapist_id":  "...",
        "confirmed_by":  "<scheduler name or ID, optional>"
      }
    """
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "").strip()
    therapist_id = data.get("therapist_id", "").strip()
    confirmed_by = data.get("confirmed_by", "scheduler").strip() or "scheduler"

    if not session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400
    if not therapist_id:
        return jsonify({"success": False, "error": "therapist_id is required"}), 400

    db = SessionLocal()
    try:
        svc = MarketplaceService(db)
        result = svc.confirm_assignment(
            session_id=session_id,
            therapist_id=therapist_id,
            confirmed_by=confirmed_by,
        )
        if not result.get("success"):
            error_msg = result.get("error", "")
            if "not found" in error_msg.lower():
                return jsonify(result), 404
            if "conflict" in error_msg.lower() or "already assigned" in error_msg.lower():
                return jsonify(result), 409
            return jsonify(result), 400
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()
