import uuid
from datetime import datetime, timezone
from app.extensions import db


class ProjectPayment(db.Model):
    __tablename__ = "project_payments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = db.Column(db.String(36), db.ForeignKey("project_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    milestone_id = db.Column(db.String(36), db.ForeignKey("project_milestones.id", ondelete="SET NULL"), nullable=True, index=True)

    payment_type = db.Column(db.String(30), default="milestone", nullable=False)  # 'deposit', 'milestone', 'final'
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, default=0.0, nullable=False)
    currency = db.Column(db.String(10), default="USD", nullable=False)
    status = db.Column(db.String(30), default="held_in_escrow", nullable=False, index=True)  # 'held_in_escrow', 'released', 'refunded'
    
    transaction_reference = db.Column(db.String(64), unique=True, nullable=False, index=True)
    payment_method = db.Column(db.String(60), default="Simulated Escrow Card (•••• 4242)", nullable=False)
    payer_name = db.Column(db.String(120), nullable=False)
    payer_email = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    released_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    project_request = db.relationship(
        "ProjectRequest",
        backref=db.backref("payments", cascade="all, delete-orphan", lazy="dynamic", order_by="ProjectPayment.created_at.desc()"),
    )
    group = db.relationship(
        "Group",
        backref=db.backref("payments", cascade="all, delete-orphan", lazy="dynamic", order_by="ProjectPayment.created_at.desc()"),
    )
    milestone = db.relationship(
        "ProjectMilestone",
        backref=db.backref("payments", lazy="dynamic"),
    )

    def release(self):
        self.status = "released"
        self.released_at = datetime.now(timezone.utc)
        if self.milestone:
            self.milestone.escrow_status = "released"

    def to_dict(self):
        return {
            "id": self.id,
            "project_request_id": self.project_request_id,
            "group_id": self.group_id,
            "group_name": self.group.name if self.group else "Squad",
            "milestone_id": self.milestone_id,
            "payment_type": self.payment_type,
            "title": self.title,
            "amount": self.amount,
            "amount_formatted": f"${self.amount:,.2f}",
            "currency": self.currency,
            "status": self.status,
            "transaction_reference": self.transaction_reference,
            "payment_method": self.payment_method,
            "payer_name": self.payer_name,
            "payer_email": self.payer_email,
            "created_at": self.created_at.strftime("%b %d, %Y, %I:%M %p") if self.created_at else "",
            "released_at": self.released_at.strftime("%b %d, %Y, %I:%M %p") if self.released_at else None,
        }

    def __repr__(self):
        return f"<ProjectPayment {self.transaction_reference} - ${self.amount:,.2f} ({self.status})>"
