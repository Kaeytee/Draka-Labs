def query_audit_logs(user_id=None, action=None, start_time=None, end_time=None, limit=100):
    """
    Query audit logs with optional filters for user, action, and time range.
    Returns a list of dicts for admin use.
    """
    db = SessionLocal()
    try:
        query = db.query(AuditLog)
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if action is not None:
            query = query.filter(AuditLog.action == action)
        if start_time is not None:
            query = query.filter(AuditLog.timestamp >= start_time)
        if end_time is not None:
            query = query.filter(AuditLog.timestamp <= end_time)
        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)
        logs = query.all()
        return [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "details": log.details,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None
            }
            for log in logs
        ]
    finally:
        db.close()
from database.db import SessionLocal
from models.audit_log import AuditLog

def log_audit(user_id, action, details=None):
    """
    Create an audit log entry for any action or process.
    Args:
        user_id (int or None): The user performing the action (None for system actions)
        action (str): Short description of the action
        details (str or None): Optional details (JSON or string)
    """
    db = SessionLocal()
    try:
        log = AuditLog(user_id=user_id, action=action, details=details)
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
