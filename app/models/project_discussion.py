import uuid
from datetime import datetime, timezone
from app.extensions import db


class ProjectDiscussionMessage(db.Model):
    __tablename__ = "project_discussion_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = db.Column(db.String(36), db.ForeignKey("project_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_type = db.Column(db.String(20), nullable=False, index=True)  # 'client', 'coder', 'admin', 'system'
    sender_name = db.Column(db.String(120), nullable=False)
    sender_coder_id = db.Column(db.String(36), db.ForeignKey("coder_users.id", ondelete="SET NULL"), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    project_request = db.relationship("ProjectRequest", backref=db.backref("discussion_messages", cascade="all, delete-orphan", lazy="dynamic", order_by="ProjectDiscussionMessage.created_at.asc()"))
    sender_coder = db.relationship("CoderUser", backref=db.backref("discussion_messages", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "project_request_id": self.project_request_id,
            "sender_type": self.sender_type,
            "sender_name": self.sender_name,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "time_formatted": self.created_at.strftime("%b %d, %I:%M %p") if self.created_at else "",
        }

    def __repr__(self):
        return f"<ProjectDiscussionMessage id={self.id} sender={self.sender_name} type={self.sender_type}>"
