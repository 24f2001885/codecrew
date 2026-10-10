from flask import request, has_request_context
from app.extensions import db
from app.models.audit_log import AuditLog


def record_audit(actor_type, actor_id, action, target_type=None, target_id=None, details=None, ip_address=None, summary=None):
    """
    Appends an audit log entry within the active database session.
    Must be called within the same transaction as the auditable action.
    """
    if ip_address is None and has_request_context():
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        if ip_address and "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

    if summary is None:
        summary = f"{action} on {target_type or 'resource'}:{target_id or ''}".strip(":")

    log_entry = AuditLog(
        actor_type=str(actor_type),
        actor_id=str(actor_id) if actor_id else None,
        action=str(action),
        target_type=str(target_type) if target_type else None,
        target_id=str(target_id) if target_id else None,
        summary=summary,
        details=details or {},
        ip_address=ip_address,
    )
    db.session.add(log_entry)
    return log_entry
