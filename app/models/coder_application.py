import uuid
from datetime import datetime
from app.extensions import db


class CoderApplication(db.Model):
    __tablename__ = "coder_applications"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    project_types = db.Column(db.JSON, default=list, nullable=False)
    domain_tags = db.Column(db.JSON, default=list, nullable=False)
    headline = db.Column(db.String(160), nullable=True)
    portfolio_url = db.Column(db.String(255), nullable=True)
    message = db.Column(db.Text, nullable=True)
    resume_pdf = db.Column(db.String(255), nullable=True)
    alerts_consent = db.Column(db.Boolean, nullable=False, default=False)
    consent_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    email_verified_at = db.Column(db.DateTime, nullable=True)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.Enum("pending", "approved", "rejected", "converted", name="application_status"),
        nullable=False,
        default="pending",
        index=True,
    )
    converted_coder_id = db.Column(
        db.String(36),
        db.ForeignKey("coder_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    converted_coder = db.relationship("CoderUser", foreign_keys=[converted_coder_id], backref="source_application")
    deliveries = db.relationship("DomainAlertDelivery", back_populates="application", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def is_verified(self):
        return self.email_verified_at is not None

    @property
    def is_unsubscribed(self):
        return self.unsubscribed_at is not None

    def __repr__(self):
        return f"<CoderApplication id={self.id} email={self.email} status={self.status}>"
