from datetime import datetime
from sqlalchemy.orm import Session as OrmSession
from app.models.notification import Notification
from app.models.session import Session as SessionModel
from app.models.therapist import Therapist


class NotificationService:
    def __init__(self, db: OrmSession):
        self.db = db

    def notify_user(self, user_id: str, session_id: str, notification_type: str, message: str) -> Notification:
        """
        Create and store a notification for a specific user.
        
        Args:
            user_id: therapist_id or family user_id
            session_id: FK to session
            notification_type: Type of notification (e.g., SESSION_ASSIGNED, SESSION_CANCELED)
            message: Human-readable message for the notification
        
        Returns:
            Notification object if created, None if session doesn't exist
        """
        session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            return None

        notification = Notification(
            user_id=user_id,
            session_id=session_id,
            type=notification_type,
            message=message,
            read=False,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def notify_therapist(self, therapist_id: str, session_id: str, notification_type: str, message: str) -> Notification:
        """Shortcut to notify a therapist."""
        return self.notify_user(therapist_id, session_id, notification_type, message)

    def notify_family(self, patient_id: str, session_id: str, notification_type: str, message: str):
        """
        Notify family members associated with a patient.
        For now, we'll use patient_id as the family user_id.
        In a production system, this would lookup all family members linked to patient_id.
        
        Returns:
            List of created Notification objects
        """
        # In a real system, you'd query a family_members table to find all family users for this patient
        # For now, we use patient_id as a family user identifier
        notification_list = []
        
        notification = self.notify_user(f"family:{patient_id}", session_id, notification_type, message)
        if notification:
            notification_list.append(notification)
        
        return notification_list

    def get_notifications(self, user_id: str, unread_only: bool = False):
        """
        Get all notifications for a user, ordered by most recent first.
        
        Args:
            user_id: therapist_id or family user_id
            unread_only: If True, return only unread notifications
        
        Returns:
            List of notification dicts with all fields
        """
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        
        if unread_only:
            query = query.filter(Notification.read == False)
        
        notifications = query.order_by(Notification.created_at.desc()).all()
        
        return [self._serialize_notification(n) for n in notifications]

    def mark_as_read(self, notification_id: int) -> bool:
        """
        Mark a notification as read.
        
        Returns:
            True if successful, False if notification not found
        """
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return False

        notification.read = True
        self.db.commit()
        self.db.refresh(notification)
        return True

    def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all unread notifications for a user as read.
        
        Returns:
            Count of notifications marked as read
        """
        unread = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False,
        ).all()

        count = len(unread)
        for notification in unread:
            notification.read = True
        
        self.db.commit()
        return count

    def delete_notification(self, notification_id: int) -> bool:
        """
        Delete a notification.
        
        Returns:
            True if successful, False if notification not found
        """
        notification = self.db.query(Notification).filter(Notification.id == notification_id).first()
        if not notification:
            return False

        self.db.delete(notification)
        self.db.commit()
        return True

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        return self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.read == False,
        ).count()

    def _serialize_notification(self, notification: Notification) -> dict:
        """Serialize a notification to a dictionary."""
        return {
            "id": notification.id,
            "user_id": notification.user_id,
            "session_id": notification.session_id,
            "type": notification.type,
            "message": notification.message,
            "created_at": notification.created_at.isoformat(),
            "read": notification.read,
        }
