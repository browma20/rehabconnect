from datetime import datetime
from sqlalchemy.orm import Session as OrmSession
from app.models.session_audit_log import SessionAuditLog


class SessionAuditService:
    def __init__(self, db: OrmSession):
        self.db = db

    def log_action(
        self,
        session_id: str,
        action_type: str,
        performed_by: str,
        old_values: dict | None = None,
        new_values: dict | None = None,
        notes: str | None = None,
    ):
        """
        Log a session action to the audit log.

        Parameters
        ----------
        session_id : str
            The ID of the session being audited.
        action_type : str
            Type of action (e.g., "created", "assigned", "completed", "canceled", "rescheduled").
        performed_by : str
            Who/what performed the action (e.g., "therapist:T100", "scheduler:admin", "system:auto").
        old_values : dict, optional
            Dictionary of values before the action.
        new_values : dict, optional
            Dictionary of values after the action.
        notes : str, optional
            Additional notes about the action.
        """
        audit_entry = SessionAuditLog(
            session_id=session_id,
            action_type=action_type,
            performed_by=performed_by,
            timestamp=datetime.utcnow(),
            old_values=old_values,
            new_values=new_values,
            notes=notes,
        )
        self.db.add(audit_entry)
        self.db.commit()

    def get_audit_log(self, session_id: str):
        """
        Retrieve all audit log entries for a session ordered by timestamp DESC.
        """
        logs = (
            self.db.query(SessionAuditLog)
            .filter(SessionAuditLog.session_id == session_id)
            .order_by(SessionAuditLog.timestamp.desc())
            .all()
        )
        return [
            {
                "id": log.id,
                "session_id": log.session_id,
                "action_type": log.action_type,
                "performed_by": log.performed_by,
                "timestamp": log.timestamp.isoformat(),
                "old_values": log.old_values,
                "new_values": log.new_values,
                "notes": log.notes,
            }
            for log in logs
        ]
