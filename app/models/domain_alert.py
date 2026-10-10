import uuid
from datetime import datetime
from app.extensions import db


class DomainAlert(db.Model):
    __tablename__ = "domain_alerts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = db.Column(
        db.String(36),
        db.ForeignKey("project_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    summary = db.Column(db.String(600), nullable=False)
    project_type_snapshot = db.Column(db.String(30), nullable=False)
    domain_tags_snapshot = db.Column(db.JSON, default=list, nullable=False)
    is_auto = db.Column(db.Boolean, default=False, nullable=False)
    sent_by_admin_id = db.Column(
        db.String(36),
        db.ForeignKey("admin_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    recipient_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    project_request = db.relationship("ProjectRequest", backref=db.backref("domain_alerts", cascade="all, delete-orphan", lazy="dynamic"))
    sent_by_admin = db.relationship("AdminUser", foreign_keys=[sent_by_admin_id])
    deliveries = db.relationship("DomainAlertDelivery", back_populates="alert", cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return f"<DomainAlert id={self.id} request_id={self.project_request_id} recipients={self.recipient_count}>"
