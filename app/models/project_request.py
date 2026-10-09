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

    def __repr__(self):
        return f"<ProjectRequest from {self.name} ({self.status})>"
