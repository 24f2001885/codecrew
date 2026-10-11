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

    # Site branding & text
    site_name = db.Column(db.String(100), default="CodeCrews", nullable=False)
    site_tagline = db.Column(db.String(255), nullable=True)
    footer_copyright = db.Column(db.String(150), nullable=True)

    # Promo / Coder pool banner
    coder_banner_enabled = db.Column(db.Boolean, default=True, nullable=False)
    coder_banner_text = db.Column(db.String(255), nullable=True)
    coder_banner_cta = db.Column(db.String(60), nullable=True)

    # Homepage Sections (Spotlight & Explore)
    spotlight_badge = db.Column(db.String(60), default="Spotlight", nullable=True)
    spotlight_title = db.Column(db.String(120), default="Featured Groups", nullable=True)
    spotlight_subtitle = db.Column(db.String(255), default="Top-ranked squads actively delivering high-impact software.", nullable=True)
    explore_title = db.Column(db.String(120), default="Explore Groups", nullable=True)
    explore_subtitle = db.Column(db.String(255), default="Browse through innovative student engineering teams across disciplines.", nullable=True)

    coder_applications_open = db.Column(db.Boolean, default=True, nullable=False)
    auto_send_domain_alerts = db.Column(db.Boolean, default=False, nullable=False)
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
