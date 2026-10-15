import uuid
from datetime import datetime, timezone
from app.extensions import db


class ProjectMilestone(db.Model):
    __tablename__ = "project_milestones"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = db.Column(db.String(36), db.ForeignKey("project_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_coder_id = db.Column(db.String(36), db.ForeignKey("coder_users.id", ondelete="SET NULL"), nullable=True, index=True)

    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="in_progress", nullable=False, index=True)  # 'in_progress', 'submitted', 'completed'
    
    deliverable_url = db.Column(db.String(255), nullable=True)
    deliverable_notes = db.Column(db.Text, nullable=True)

    submitted_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project_request = db.relationship(
        "ProjectRequest",
        backref=db.backref("milestones", cascade="all, delete-orphan", lazy="dynamic", order_by="ProjectMilestone.created_at.asc()"),
    )
    created_by_coder = db.relationship("CoderUser", backref=db.backref("milestones_created", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "project_request_id": self.project_request_id,
            "title": self.title,
            "description": self.description or "",
            "status": self.status,
            "deliverable_url": self.deliverable_url or "",
            "deliverable_notes": self.deliverable_notes or "",
            "submitted_at": self.submitted_at.strftime("%b %d, %Y") if self.submitted_at else None,
            "completed_at": self.completed_at.strftime("%b %d, %Y") if self.completed_at else None,
            "created_at": self.created_at.strftime("%b %d, %Y") if self.created_at else "",
        }

    def __repr__(self):
        return f"<ProjectMilestone id={self.id} title={self.title!r} status={self.status}>"
