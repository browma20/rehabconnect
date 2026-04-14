from flask import Blueprint, request, jsonify
from datetime import date
from backend.app.database import SessionLocal
from backend.app.services.staffing_prediction_service import StaffingPredictionService
from backend.app.services.load_balancing_service import LoadBalancingService

staffing_bp = Blueprint('staffing', __name__)


@staffing_bp.route('/staffing/predict', methods=['GET'])
def predict_staffing():
    week_start_str = request.args.get('week_start')
    days_str = request.args.get('days', '7')

    if not week_start_str:
        return jsonify({"error": "week_start is required (YYYY-MM-DD)"}), 400

    try:
        week_start = date.fromisoformat(week_start_str)
    except ValueError:
        return jsonify({"error": "Invalid week_start format, expected YYYY-MM-DD"}), 400

    try:
        days = int(days_str)
        if days < 1 or days > 365:
            raise ValueError
    except ValueError:
        return jsonify({"error": "days must be a positive integer between 1 and 365"}), 400

    db = SessionLocal()
    try:
        service = StaffingPredictionService(db)
        result = service.predict_staffing(week_start, days)
        return jsonify(result), 200
    finally:
        db.close()


@staffing_bp.route('/staffing/balance', methods=['POST'])
def balance_staffing():
    week_start_str = request.args.get('week_start')
    days_str = request.args.get('days', '7')

    if not week_start_str:
        return jsonify({"error": "week_start is required (YYYY-MM-DD)"}), 400

    try:
        week_start = date.fromisoformat(week_start_str)
    except ValueError:
        return jsonify({"error": "Invalid week_start format, expected YYYY-MM-DD"}), 400

    try:
        days = int(days_str)
        if days < 1 or days > 365:
            raise ValueError
    except ValueError:
        return jsonify({"error": "days must be a positive integer between 1 and 365"}), 400

    db = SessionLocal()
    try:
        service = LoadBalancingService(db)
        result = service.balance_load(week_start, days)
        return jsonify(result), 200
    finally:
        db.close()
