import uuid
from datetime import datetime
from app.extensions import db


class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(140), unique=True, nullable=False, index=True)
    tagline = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    logo_path = db.Column(db.String(255), nullable=True)
    cover_image_path = db.Column(db.String(255), nullable=True)
    founded_year = db.Column(db.Integer, nullable=True)
    founded_date = db.Column(db.Date, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    tech_tags = db.Column(db.JSON, default=list, nullable=False)
    social_links = db.Column(db.JSON, default=dict, nullable=False)
    featured = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = db.relationship("Member", backref="group", cascade="all, delete-orphan", lazy="dynamic", order_by="Member.display_order")
    projects = db.relationship("Project", backref="group", cascade="all, delete-orphan", lazy="dynamic")
    blog_posts = db.relationship("BlogPost", backref="group", cascade="all, delete-orphan", lazy="dynamic")
    contact_messages = db.relationship("ContactMessage", backref="group", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def logo(self):
        return self.logo_path

    @logo.setter
    def logo(self, val):
        self.logo_path = val

    @property
    def cover_image(self):
        return self.cover_image_path

    @cover_image.setter
    def cover_image(self, val):
        self.cover_image_path = val

    def __repr__(self):
        return f"<Group {self.name} ({self.slug})>"
