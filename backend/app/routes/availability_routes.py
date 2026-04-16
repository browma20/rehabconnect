from flask import Blueprint, request, jsonify
from app.database import SessionLocal
from app.services.availability_service import AvailabilityService

availability_bp = Blueprint('availability', __name__)


@availability_bp.route('/therapists/<therapist_id>/availability', methods=['GET'])
def get_availability(therapist_id):
    db = SessionLocal()
    try:
        service = AvailabilityService(db)
        blocks = service.get_availability_for_therapist(therapist_id)
        return jsonify({"therapist_id": therapist_id, "availability": blocks}), 200
    finally:
        db.close()


@availability_bp.route('/therapists/<therapist_id>/availability', methods=['POST'])
def add_availability(therapist_id):
    data = request.get_json()
    db = SessionLocal()
    try:
        service = AvailabilityService(db)
        block = service.add_availability_block(therapist_id, data)
        return jsonify(block), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@availability_bp.route('/therapists/<therapist_id>/availability/<availability_id>', methods=['DELETE'])
def delete_availability(therapist_id, availability_id):
    db = SessionLocal()
    try:
        service = AvailabilityService(db)
        success = service.delete_availability_block(availability_id)
        if not success:
            return jsonify({"error": "Availability block not found"}), 404
        return jsonify({"message": "Availability block deleted"}), 200
    finally:
        db.close()


@availability_bp.route('/therapists/<therapist_id>/time-off', methods=['GET'])
def get_time_off(therapist_id):
    db = SessionLocal()
    try:
        service = AvailabilityService(db)
        blocks = service.get_time_off_for_therapist(therapist_id)
        return jsonify({"therapist_id": therapist_id, "time_off": blocks}), 200
    finally:
        db.close()


@availability_bp.route('/therapists/<therapist_id>/time-off', methods=['POST'])
def add_time_off(therapist_id):
    data = request.get_json()
    db = SessionLocal()
    try:
        service = AvailabilityService(db)
        block = service.add_time_off_block(therapist_id, data)
        return jsonify(block), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


@availability_bp.route('/therapists/<therapist_id>/time-off/<time_off_id>', methods=['DELETE'])
def delete_time_off(therapist_id, time_off_id):
    db = SessionLocal()
    try:
        service = AvailabilityService(db)
        success = service.delete_time_off_block(time_off_id)
        if not success:
            return jsonify({"error": "Time off block not found"}), 404
        return jsonify({"message": "Time off block deleted"}), 200
    finally:
        db.close()
