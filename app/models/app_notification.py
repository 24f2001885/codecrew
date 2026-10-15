import uuid
from datetime import datetime, timezone
from app.extensions import db


class AppNotification(db.Model):
    __tablename__ = "app_notifications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_type = db.Column(db.String(20), nullable=False, index=True)  # 'coder', 'admin', 'client'
    recipient_id = db.Column(db.String(36), nullable=True, index=True)      # coder_id, admin_id, or project_request_id

    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link_url = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), default="system", nullable=False, index=True)  # 'message', 'offer', 'milestone', 'review', 'system'
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "recipient_type": self.recipient_type,
            "recipient_id": self.recipient_id,
            "title": self.title,
            "message": self.message,
            "link_url": self.link_url or "#",
            "category": self.category,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%b %d, %H:%M") if self.created_at else "",
            "time_ago": self.time_ago(),
        }

    def time_ago(self):
        if not self.created_at:
            return ""
        now = datetime.now(timezone.utc)
        created = self.created_at.replace(tzinfo=timezone.utc) if self.created_at.tzinfo is None else self.created_at
        diff = now - created
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"

    def __repr__(self):
        return f"<AppNotification id={self.id} recipient={self.recipient_type}:{self.recipient_id} read={self.is_read}>"
