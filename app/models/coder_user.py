import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import synonym
from app.extensions import db


class CoderUser(UserMixin, db.Model):
    __tablename__ = "coder_users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = db.Column(db.String(36), db.ForeignKey("members.id", ondelete="CASCADE"), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="invited", index=True)  # 'invited', 'active', 'revoked'

    created_by_admin_id = db.Column(db.String(36), db.ForeignKey("admin_users.id"), nullable=True)
    invite_sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)
    activated_at = db.Column(db.DateTime, nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked_by_admin_id = db.Column(db.String(36), db.ForeignKey("admin_users.id"), nullable=True)
    revoke_reason = db.Column(db.String(300), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Synonyms for backwards/forwards compatibility
    invited_at = synonym("invite_sent_at")
    revoked_reason = synonym("revoke_reason")

    # Relationships
    member = db.relationship("Member", backref=db.backref("coder_account", uselist=False))
    created_by_admin = db.relationship("AdminUser", foreign_keys=[created_by_admin_id], backref="created_coders")
    revoked_by_admin = db.relationship("AdminUser", foreign_keys=[revoked_by_admin_id], backref="revoked_coders")

    role = "coder"

    @property
    def is_active(self):
        return self.status == "active"

    @property
    def group(self):
        return self.member.group if self.member and hasattr(self.member, "group") else None

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"coder:{self.id}"

    def __repr__(self):
        return f"<CoderUser username={self.username} status={self.status}>"
