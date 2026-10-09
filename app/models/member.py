import uuid
from datetime import datetime
from app.extensions import db


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    photo = db.Column(db.String(255), nullable=True)
    resume_pdf = db.Column(db.String(255), nullable=True)
    skill_tags = db.Column(db.JSON, default=list)
    github_url = db.Column(db.String(255), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    twitter_url = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Member {self.name} ({self.role})>"
