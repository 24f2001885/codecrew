from datetime import datetime
from app.extensions import db


class SiteSettings(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True, default=1)
    hero_title = db.Column(db.String(200), nullable=True)
    hero_subtitle = db.Column(db.String(300), nullable=True)
    footer_text = db.Column(db.String(300), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    stats_override = db.Column(db.JSON, default=dict)
    seo_meta_description = db.Column(db.String(300), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @classmethod
    def get_settings(cls):
        settings = cls.query.get(1)
        if not settings:
            settings = cls(id=1)
            db.session.add(settings)
            db.session.commit()
        return settings

    def __repr__(self):
        return f"<SiteSettings id={self.id}>"
