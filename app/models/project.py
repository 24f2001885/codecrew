import uuid
from datetime import datetime
from app.extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), nullable=True, index=True)
    summary = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)
    screenshot = db.Column(db.String(255), nullable=True)
    demo_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    tech_tags = db.Column(db.JSON, default=list)
    featured = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Project {self.title}>"
