import uuid
from datetime import datetime, timezone
from app.extensions import db


class GroupChatMessage(db.Model):
    __tablename__ = "group_chat_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    coder_id = db.Column(db.String(36), db.ForeignKey("coder_users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    group = db.relationship("Group", backref=db.backref("chat_messages", cascade="all, delete-orphan", lazy="dynamic", order_by="GroupChatMessage.created_at.asc()"))
    coder = db.relationship("CoderUser", backref=db.backref("chat_messages", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "coder_id": self.coder_id,
            "username": self.coder.username if self.coder else "Unknown",
            "member_name": self.coder.member.name if self.coder and self.coder.member else (self.coder.username if self.coder else "Coder"),
            "role": self.coder.member.role if self.coder and self.coder.member else "Member",
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "time_formatted": self.created_at.strftime("%I:%M %p") if self.created_at else "",
        }

    def __repr__(self):
        return f"<GroupChatMessage id={self.id} group_id={self.group_id} coder_id={self.coder_id}>"
