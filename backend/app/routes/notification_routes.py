from flask import Blueprint, request, jsonify
from backend.app.database import SessionLocal
from backend.app.services.notification_service import NotificationService


notification_bp = Blueprint('notification', __name__)


@notification_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """
    Get all notifications for the current user.
    Query parameters:
      - user_id (required): therapist_id or family user_id
      - unread_only (optional, default=False): if true, only return unread notifications
    """
    user_id = request.args.get('user_id')
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    db = SessionLocal()
    try:
        service = NotificationService(db)
        notifications = service.get_notifications(user_id, unread_only=unread_only)
        return jsonify({
            "user_id": user_id,
            "unread_only": unread_only,
            "count": len(notifications),
            "notifications": notifications,
        }), 200
    finally:
        db.close()


@notification_bp.route('/notifications/unread-count', methods=['GET'])
def get_unread_count():
    """
    Get count of unread notifications for the current user.
    Query parameters:
      - user_id (required): therapist_id or family user_id
    """
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    db = SessionLocal()
    try:
        service = NotificationService(db)
        count = service.get_unread_count(user_id)
        return jsonify({
            "user_id": user_id,
            "unread_count": count,
        }), 200
    finally:
        db.close()


@notification_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
def mark_as_read(notification_id):
    """Mark a single notification as read."""
    db = SessionLocal()
    try:
        service = NotificationService(db)
        success = service.mark_as_read(notification_id)
        if not success:
            return jsonify({"error": "Notification not found"}), 404
        
        return jsonify({"message": "Notification marked as read", "notification_id": notification_id}), 200
    finally:
        db.close()


@notification_bp.route('/notifications/mark-all-read', methods=['POST'])
def mark_all_as_read():
    """
    Mark all unread notifications for a user as read.
    JSON body:
      - user_id (required): therapist_id or family user_id
    """
    data = request.get_json() or {}
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    db = SessionLocal()
    try:
        service = NotificationService(db)
        count = service.mark_all_as_read(user_id)
        return jsonify({
            "message": f"Marked {count} notifications as read",
            "user_id": user_id,
            "marked_count": count,
        }), 200
    finally:
        db.close()


@notification_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification."""
    db = SessionLocal()
    try:
        service = NotificationService(db)
        success = service.delete_notification(notification_id)
        if not success:
            return jsonify({"error": "Notification not found"}), 404
        
        return jsonify({"message": "Notification deleted", "notification_id": notification_id}), 200
    finally:
        db.close()
