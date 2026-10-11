from app.extensions import db
from app.models.site_settings import SiteSettings
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project


def get_site_settings():
    """
    Returns the singleton SiteSettings row or a transient (unsaved) object with defaults.
    Never creates database rows during a GET lookup.
    """
    try:
        row = db.session.get(SiteSettings, 1)
        if row is not None:
            return row
    except Exception:
        pass

    return SiteSettings(
        id=1,
        site_name="CodeCrews",
        site_tagline="The premier multi-tenant developer agency showcasing high-performing student engineering teams, collaborative projects, and world-class craft.",
        footer_copyright="CodeCrews. All rights reserved.",
        hero_headline="Discover the Teams Building Tomorrow",
        hero_subheadline="CodeCrews brings together high-performing student developer collectives, production portfolios, and modern engineering crafts in one unified ecosystem.",
        hero_cta_text="Browse Groups",
        hero_images=[],
        coder_banner_enabled=True,
        coder_banner_text="Developer? Join our coder pool and hear about projects in your domain.",
        coder_banner_cta="Join as a Coder",
        spotlight_badge="Spotlight",
        spotlight_title="Featured Groups",
        spotlight_subtitle="Top-ranked squads actively delivering high-impact software.",
        explore_title="Explore Groups",
        explore_subtitle="Browse through innovative student engineering teams across disciplines.",
        footer_social_links={},
        seo_default_title="CodeCrews",
        seo_default_description="A directory of coding teams.",
        seo_default_og_image=None,
        stats_override=None,
    )


def platform_stats():
    """
    Returns the platform counts, honoring stats_override if configured.
    """
    try:
        settings = get_site_settings()
        if settings and settings.stats_override:
            override = settings.stats_override
            return {
                "groups": override.get("total_groups", 0),
                "members": override.get("total_members", 0),
                "projects": override.get("total_projects", 0),
            }
        return {
            "groups": Group.query.count(),
            "members": Member.query.count(),
            "projects": Project.query.count(),
        }
    except Exception:
        return {
            "groups": 0,
            "members": 0,
            "projects": 0,
        }


def seo_for(page_title=None, description=None, og_image=None):
    """
    Computes SEO metadata using page overrides first, then SiteSettings defaults,
    then hard-coded system fallbacks.
    """
    try:
        settings = get_site_settings()
        title = page_title or getattr(settings, "seo_default_title", None) or "CodeCrews"
        desc = description or getattr(settings, "seo_default_description", None) or "A directory of coding teams."
        image = og_image or getattr(settings, "seo_default_og_image", None) or None
    except Exception:
        title = page_title or "CodeCrews"
        desc = description or "A directory of coding teams."
        image = og_image

    return {
        "title": title,
        "description": desc,
        "og_image": image,
    }

