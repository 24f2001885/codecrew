import uuid
from datetime import datetime
from app.extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(170), nullable=False, index=True)
    summary = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default="completed", nullable=False)
    gallery_images = db.Column(db.JSON, default=list, nullable=False)
    tech_tags = db.Column(db.JSON, default=list, nullable=False)
    screenshot = db.Column(db.String(255), nullable=True)
    demo_url = db.Column(db.String(255), nullable=True)
    live_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    featured = db.Column(db.Boolean, default=False, nullable=False)
    created_by_coder_id = db.Column(db.String(36), db.ForeignKey("coder_users.id", ondelete="SET NULL"), nullable=True)
    last_edited_by_coder_id = db.Column(db.String(36), db.ForeignKey("coder_users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    __table_args__ = (
        db.UniqueConstraint("group_id", "slug", name="uq_project_group_slug"),
    )

    def __repr__(self):
        return f"<Project {self.title}>"
