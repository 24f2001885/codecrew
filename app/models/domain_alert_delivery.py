import uuid
from datetime import datetime
from app.extensions import db


class DomainAlertDelivery(db.Model):
    __tablename__ = "domain_alert_deliveries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = db.Column(
        db.String(36),
        db.ForeignKey("domain_alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id = db.Column(
        db.String(36),
        db.ForeignKey("coder_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = db.Column(
        db.Enum("sent", "failed", name="delivery_status"),
        nullable=False,
        default="sent",
    )
    error = db.Column(db.String(255), nullable=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    interested_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("alert_id", "application_id", name="uq_alert_application"),
    )

    alert = db.relationship("DomainAlert", back_populates="deliveries")
    application = db.relationship("CoderApplication", back_populates="deliveries")

    def __repr__(self):
        return f"<DomainAlertDelivery id={self.id} alert={self.alert_id} app={self.application_id} status={self.status}>"
