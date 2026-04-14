from flask import Blueprint, request, jsonify
from backend.app.services.therapist_service import TherapistService
from backend.app.services.bulk_rescheduling_service import BulkReschedulingService
from backend.app.database import SessionLocal
from backend.app.models.therapist import Therapist
from datetime import date

therapist_bp = Blueprint('therapist', __name__)

@therapist_bp.route('/therapists', methods=['POST'])
def create_therapist():
    data = request.get_json()
    db = SessionLocal()

    try:
        service = TherapistService(db)
        therapist = service.create_therapist(data)
        return jsonify({
            "therapist_id": therapist.therapist_id,
            "first_name": therapist.first_name,
            "last_name": therapist.last_name,
            "discipline": therapist.discipline,
            "active": therapist.active
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@therapist_bp.route('/therapists', methods=['GET'])
def list_therapists():
    db = SessionLocal()
    try:
        service = TherapistService(db)
        therapists = service.list_therapists()
        return jsonify([
            {
                "therapist_id": t.therapist_id,
                "first_name": t.first_name,
                "last_name": t.last_name,
                "discipline": t.discipline,
                "active": t.active
            }
            for t in therapists
        ])
    finally:
        db.close()


@therapist_bp.route('/therapists/count', methods=['GET'])
def count_therapists():
    db = SessionLocal()
    try:
        count = db.query(Therapist).count()
        return jsonify({"count": count})
    finally:
        db.close()


@therapist_bp.route('/therapists/<therapist_id>', methods=['GET'])
def get_therapist(therapist_id):
    db = SessionLocal()
    try:
        service = TherapistService(db)
        therapist = service.get_therapist_by_id(therapist_id)
        if not therapist:
            return jsonify({"error": "Therapist not found"}), 404

        return jsonify({
            "therapist_id": therapist.therapist_id,
            "first_name": therapist.first_name,
            "last_name": therapist.last_name,
            "discipline": therapist.discipline,
            "active": therapist.active
        })
    finally:
        db.close()


@therapist_bp.route('/therapists/<therapist_id>', methods=['PUT'])
def update_therapist(therapist_id):
    data = request.get_json()
    db = SessionLocal()
    try:
        service = TherapistService(db)
        therapist = service.update_therapist(therapist_id, **data)
        if not therapist:
            return jsonify({"error": "Therapist not found"}), 404

        return jsonify({
            "therapist_id": therapist.therapist_id,
            "first_name": therapist.first_name,
            "last_name": therapist.last_name,
            "discipline": therapist.discipline,
            "active": therapist.active
        })
    finally:
        db.close()


@therapist_bp.route('/therapists/<therapist_id>', methods=['DELETE'])
def delete_therapist(therapist_id):
    db = SessionLocal()
    try:
        service = TherapistService(db)
        success = service.delete_therapist(therapist_id)
        if not success:
            return jsonify({"error": "Therapist not found"}), 404

        return jsonify({"message": "Therapist deleted"})
    finally:
        db.close()


@therapist_bp.route('/therapists/<therapist_id>/bulk-reschedule', methods=['POST'])
def bulk_reschedule_therapist_sessions(therapist_id):
    data = request.get_json(silent=True) or {}

    start_date_value = data.get("start_date") or request.args.get("start_date")
    end_date_value = data.get("end_date") or request.args.get("end_date")

    if not start_date_value or not end_date_value:
        return jsonify({"success": False, "error": "start_date and end_date are required (YYYY-MM-DD)"}), 400

    try:
        start_date = date.fromisoformat(start_date_value)
        end_date = date.fromisoformat(end_date_value)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format; use YYYY-MM-DD"}), 400

    if start_date > end_date:
        return jsonify({"success": False, "error": "start_date must be less than or equal to end_date"}), 400

    db = SessionLocal()
    try:
        service = BulkReschedulingService(db)
        summary = service.bulk_reschedule(therapist_id, start_date, end_date)

        if summary.get("success") is False:
            return jsonify({"success": False, "error": summary.get("error", "Bulk reschedule failed")}), 404

        return jsonify({"success": True, "data": summary}), 200
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        db.close()