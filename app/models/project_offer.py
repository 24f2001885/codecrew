import uuid
from datetime import datetime, timezone
from app.extensions import db


class ProjectOffer(db.Model):
    __tablename__ = "project_offers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = db.Column(db.String(36), db.ForeignKey("project_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    coder_id = db.Column(db.String(36), db.ForeignKey("coder_users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    proposed_budget = db.Column(db.String(80), nullable=False)
    proposed_timeline = db.Column(db.String(80), nullable=False)
    pitch = db.Column(db.Text, nullable=False)
    deliverables = db.Column(db.JSON, default=list, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False, index=True)  # 'pending', 'accepted', 'declined'

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project_request = db.relationship("ProjectRequest", backref=db.backref("offers", cascade="all, delete-orphan", lazy="dynamic", order_by="ProjectOffer.created_at.desc()"))
    group = db.relationship("Group", backref=db.backref("offers", cascade="all, delete-orphan", lazy="dynamic"))
    coder = db.relationship("CoderUser", backref=db.backref("submitted_offers", lazy="dynamic"))

    def to_dict(self):
        return {
            "id": self.id,
            "project_request_id": self.project_request_id,
            "group_id": self.group_id,
            "group_name": self.group.name if self.group else "Squad",
            "group_slug": self.group.slug if self.group else "",
            "group_tagline": self.group.tagline if self.group else "",
            "proposed_budget": self.proposed_budget,
            "proposed_timeline": self.proposed_timeline,
            "pitch": self.pitch,
            "deliverables": self.deliverables or [],
            "status": self.status,
            "created_at": self.created_at.strftime("%b %d, %Y") if self.created_at else "",
        }

    def __repr__(self):
        return f"<ProjectOffer id={self.id} request={self.project_request_id} group={self.group_id} status={self.status}>"
