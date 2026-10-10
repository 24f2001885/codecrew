import uuid
from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_type = db.Column(db.String(20), nullable=False, index=True)  # 'admin', 'coder', 'public', 'system'
    actor_id = db.Column(db.String(36), nullable=True, index=True)
    action = db.Column(db.String(60), nullable=False, index=True)
    target_type = db.Column(db.String(40), nullable=True)
    target_id = db.Column(db.String(36), nullable=True)
    summary = db.Column(db.String(300), nullable=True)
    details = db.Column(db.JSON, default=dict, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog action={self.action} actor={self.actor_type}:{self.actor_id}>"
