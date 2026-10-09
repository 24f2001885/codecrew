import uuid
from datetime import datetime
from app.extensions import db


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=True, index=True)
    content = db.Column(db.Text, nullable=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BlogPost {self.title}>"
