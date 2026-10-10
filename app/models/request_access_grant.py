import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import synonym
from app.extensions import db


class RequestAccessGrant(db.Model):
    __tablename__ = "request_access_grants"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = db.Column(db.String(36), db.ForeignKey("project_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    coder_id = db.Column(db.String(36), db.ForeignKey("coder_users.id", ondelete="CASCADE"), nullable=False, index=True)
    scope = db.Column(db.String(30), nullable=False, default="brief_only")  # 'brief_only' or 'brief_and_contact'
    expires_at = db.Column(db.DateTime, nullable=True)
    granted_by_admin_id = db.Column(db.String(36), db.ForeignKey("admin_users.id"), nullable=False)
    granted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    revoked_at = db.Column(db.DateTime, nullable=True, index=True)
    revoked_by_admin_id = db.Column(db.String(36), db.ForeignKey("admin_users.id"), nullable=True)
    revoke_reason = db.Column(db.String(300), nullable=True)

    # Synonyms for flexibility
    request_id = synonym("project_request_id")
    created_at = synonym("granted_at")
    revoked_reason = synonym("revoke_reason")

    # Relationships
    project_request = db.relationship("ProjectRequest", backref=db.backref("grants", cascade="all, delete-orphan", lazy="dynamic"))
    coder = db.relationship("CoderUser", backref=db.backref("grants", cascade="all, delete-orphan", lazy="dynamic"))
    granted_by_admin = db.relationship("AdminUser", foreign_keys=[granted_by_admin_id], backref="granted_accesses")
    revoked_by_admin = db.relationship("AdminUser", foreign_keys=[revoked_by_admin_id], backref="revoked_accesses")

    @property
    def is_active(self):
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None:
            now = datetime.now(timezone.utc)
            exp = self.expires_at.replace(tzinfo=timezone.utc) if self.expires_at.tzinfo is None else self.expires_at
            if exp <= now:
                return False
        return True

    def __repr__(self):
        return f"<RequestAccessGrant id={self.id} scope={self.scope} active={self.is_active}>"
