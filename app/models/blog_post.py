import uuid
from datetime import datetime
from app.extensions import db


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    __table_args__ = (
        db.UniqueConstraint("group_id", "slug", name="uq_blog_posts_group_id_slug"),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = db.Column(db.String(36), db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    cover_image_path = db.Column(db.String(255), nullable=True)
    published_at = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.JSON, default=list, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    @property
    def is_published(self):
        return self.published_at is not None

    def __repr__(self):
        return f"<BlogPost {self.title}>"
