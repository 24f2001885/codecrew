import uuid
from datetime import datetime, timezone
from app.extensions import db


class SquadReview(db.Model):
    __tablename__ = "squad_reviews"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_request_id = db.Column(db.String(36), db.ForeignKey("project_requests.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)

    client_name = db.Column(db.String(100), nullable=False)
    client_company = db.Column(db.String(120), nullable=True)
    rating = db.Column(db.Integer, nullable=False, default=5)
    review_title = db.Column(db.String(150), nullable=True)
    comment = db.Column(db.Text, nullable=False)
    verified = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    project_request = db.relationship("ProjectRequest", backref=db.backref("review", uselist=False, cascade="all, delete-orphan"))
    group = db.relationship("Group", backref=db.backref("reviews", cascade="all, delete-orphan", lazy="dynamic", order_by="SquadReview.created_at.desc()"))

    def to_dict(self):
        return {
            "id": self.id,
            "project_request_id": self.project_request_id,
            "group_id": self.group_id,
            "group_name": self.group.name if self.group else "Squad",
            "client_name": self.client_name,
            "client_company": self.client_company or "",
            "rating": self.rating,
            "review_title": self.review_title or "",
            "comment": self.comment,
            "verified": self.verified,
            "created_at": self.created_at.strftime("%b %d, %Y") if self.created_at else "",
        }

    def __repr__(self):
        return f"<SquadReview id={self.id} group={self.group_id} rating={self.rating}>"
