from flask import Blueprint, jsonify, request

from app.database import SessionLocal
from app.services.automation_suggestion_service import AutomationSuggestionService

automation_bp = Blueprint("automation", __name__)


@automation_bp.route("/automation/suggest-assignment", methods=["POST"])
def suggest_assignment():
    data = request.get_json(silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    performed_by = (data.get("performed_by") or "").strip() or None

    if not session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400

    db = SessionLocal()
    try:
        service = AutomationSuggestionService(db)
        result = service.suggest_assignment(session_id, performed_by=performed_by)
        if not result.get("success"):
            status = 404 if "not found" in (result.get("error") or "").lower() else 400
            return (
                jsonify(
                    {
                        "success": False,
                        "error": result.get("error", "Unable to generate assignment suggestion"),
                        "details": result,
                    }
                ),
                status,
            )
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": f"suggest_assignment_failed: {exc}"}), 500
    finally:
        db.close()


@automation_bp.route("/automation/suggest-reschedule", methods=["POST"])
def suggest_reschedule():
    data = request.get_json(silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    performed_by = (data.get("performed_by") or "").strip() or None

    if not session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400

    db = SessionLocal()
    try:
        service = AutomationSuggestionService(db)
        result = service.suggest_reschedule(session_id, performed_by=performed_by)
        if not result.get("success"):
            status = 404 if "not found" in (result.get("error") or "").lower() else 400
            return jsonify(result), status
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()


@automation_bp.route("/automation/override", methods=["POST"])
def log_override():
    data = request.get_json(silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    recommended_therapist_id = (data.get("recommended_therapist_id") or "").strip()
    chosen_therapist_id = (data.get("chosen_therapist_id") or "").strip()
    reason = (data.get("reason") or "").strip()
    metadata = data.get("metadata") or {}

    if not session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400
    if not recommended_therapist_id:
        return jsonify({"success": False, "error": "recommended_therapist_id is required"}), 400
    if not chosen_therapist_id:
        return jsonify({"success": False, "error": "chosen_therapist_id is required"}), 400
    if not reason:
        return jsonify({"success": False, "error": "reason is required"}), 400

    db = SessionLocal()
    try:
        service = AutomationSuggestionService(db)
        result = service.log_override(
            session_id=session_id,
            recommended_therapist_id=recommended_therapist_id,
            chosen_therapist_id=chosen_therapist_id,
            reason=reason,
            metadata=metadata,
        )
        if not result.get("success"):
            status = 404 if "not found" in (result.get("error") or "").lower() else 400
            return jsonify(result), status
        return jsonify({"success": True}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": f"override_logging_failed: {exc}"}), 500
    finally:
        db.close()


@automation_bp.route("/automation/audit/<session_id>", methods=["GET"])
def get_automation_audit(session_id):
    if not (session_id or "").strip():
        return jsonify({"success": False, "error": "session_id is required"}), 400

    db = SessionLocal()
    try:
        service = AutomationSuggestionService(db)
        entries = service.get_automation_audit_entries(session_id.strip())
        return jsonify({"success": True, "data": entries}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": f"automation_audit_failed: {exc}"}), 500
    finally:
        db.close()


@automation_bp.route("/automation/manual-action", methods=["POST"])
def log_manual_action():
    data = request.get_json(silent=True) or {}
    session_id = (data.get("session_id") or "").strip()
    event_type = (data.get("event_type") or "").strip()
    performed_by = (data.get("performed_by") or "").strip()
    human_choice = data.get("human_choice") or {}
    override_reason = (data.get("override_reason") or "").strip() or None
    metadata = data.get("metadata") or {}

    if not session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400
    if event_type not in {"manual_assignment", "manual_reschedule"}:
        return jsonify({"success": False, "error": "event_type must be manual_assignment or manual_reschedule"}), 400
    if not isinstance(human_choice, dict) or not human_choice:
        return jsonify({"success": False, "error": "human_choice is required"}), 400
    if not performed_by:
        return jsonify({"success": False, "error": "performed_by is required"}), 400

    db = SessionLocal()
    try:
        service = AutomationSuggestionService(db)
        result = service.log_manual_action(
            session_id=session_id,
            event_type=event_type,
            human_choice=human_choice,
            performed_by=performed_by,
            override_reason=override_reason,
            metadata=metadata,
        )
        if not result.get("success"):
            status = 404 if "not found" in (result.get("error") or "").lower() else 400
            return jsonify(result), status
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": f"manual_action_logging_failed: {exc}"}), 500
    finally:
        db.close()
