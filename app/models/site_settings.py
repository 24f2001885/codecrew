from datetime import datetime
from app.extensions import db


class SiteSettings(db.Model):
    __tablename__ = "site_settings"

    id = db.Column(db.Integer, primary_key=True, default=1)
    hero_headline = db.Column(db.String(200), nullable=True)
    hero_subheadline = db.Column(db.String(300), nullable=True)
    hero_cta_text = db.Column(db.String(80), nullable=True)
    hero_images = db.Column(db.JSON, default=list, nullable=False)
    footer_social_links = db.Column(db.JSON, default=dict, nullable=False)
    seo_default_title = db.Column(db.String(200), nullable=True)
    seo_default_description = db.Column(db.String(300), nullable=True)
    seo_default_og_image = db.Column(db.String(255), nullable=True)
    stats_override = db.Column(db.JSON, nullable=True)

    # Note: P7/P8 add coder_applications_open and auto_send_domain_alerts later
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @classmethod
    def get_singleton(cls):
        """Loads the single settings row, creating it if it does not yet exist."""
        row = db.session.get(cls, 1)
        if not row:
            row = cls(id=1)
            db.session.add(row)
            db.session.commit()
        return row

    @classmethod
    def get_settings(cls):
        return cls.get_singleton()

    def __repr__(self):
        return f"<SiteSettings id={self.id}>"
