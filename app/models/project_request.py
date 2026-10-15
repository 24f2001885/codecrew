import uuid
from datetime import datetime
from app.extensions import db


class ProjectRequest(db.Model):
    __tablename__ = "project_requests"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(150), nullable=True)
    project_type = db.Column(db.String(100), nullable=False)
    budget_range = db.Column(db.String(80), nullable=True)
    timeline = db.Column(db.String(80), nullable=True)
    description = db.Column(db.Text, nullable=False)
    attachment_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default="new", nullable=False)
    assigned_group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True)
    domain_tags = db.Column(db.JSON, default=list)
    internal_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    assigned_group = db.relationship("Group", backref=db.backref("assigned_requests", lazy="dynamic"))

    @property
    def attachment(self):
        return self.attachment_path

    @attachment.setter
    def attachment(self, val):
        self.attachment_path = val

    @property
    def active_offers(self):
        return self.offers.filter_by(status="pending").all()

    @property
    def accepted_offer(self):
        return self.offers.filter_by(status="accepted").first()

    @property
    def progress_percentage(self):
        total = self.milestones.count()
        if total == 0:
            return 0
        completed = self.milestones.filter_by(status="completed").count()
        return int((completed / total) * 100)

    @property
    def active_milestones(self):
        return self.milestones.all()

    @property
    def total_escrow_funded(self):
        return sum(p.amount for p in self.payments.filter(db.or_(db.text("status='held_in_escrow'"), db.text("status='released'"))).all())

    @property
    def total_escrow_held(self):
        return sum(p.amount for p in self.payments.filter_by(status="held_in_escrow").all())

    @property
    def total_released_to_squad(self):
        return sum(p.amount for p in self.payments.filter_by(status="released").all())

    def __repr__(self):
        return f"<ProjectRequest from {self.name} ({self.status})>"
