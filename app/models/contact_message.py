import uuid
from datetime import datetime
from app.extensions import db


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    @property
    def sender_name(self):
        return self.name

    @sender_name.setter
    def sender_name(self, val):
        self.name = val

    @property
    def sender_email(self):
        return self.email

    @sender_email.setter
    def sender_email(self, val):
        self.email = val

    def __repr__(self):
        return f"<ContactMessage from {self.name}>"
