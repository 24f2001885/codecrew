import io
from app.extensions import db
from app.models.site_settings import SiteSettings
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project


def test_settings_requires_admin(client):
    # Anonymous access redirects to login
    resp = client.get("/admin/settings", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_settings_page_authenticated(logged_in_client):
    # Logged in admin gets 200
    resp_auth = logged_in_client.get("/admin/settings")
    assert resp_auth.status_code == 200
    assert b"Site Settings" in resp_auth.data or b"Platform Settings" in resp_auth.data



def test_save_settings_updates_singleton_only_one_row(app, logged_in_client):
    data = {
        "hero_headline": "Custom Test Headline",
        "hero_subheadline": "Custom Test Subheadline",
        "hero_cta_text": "Join Us Today",
        "github_url": "https://github.com/codecrews-test",
        "twitter_url": "https://twitter.com/codecrews-test",
        "seo_default_title": "Custom Site Title",
        "seo_default_description": "Custom SEO Description",
    }
    # Save once
    resp1 = logged_in_client.post("/admin/settings", data=data, follow_redirects=True)
    assert resp1.status_code == 200
    assert b"Settings saved." in resp1.data

    with app.app_context():
        assert SiteSettings.query.count() == 1
        settings = SiteSettings.query.get(1)
        assert settings.hero_headline == "Custom Test Headline"
        assert settings.footer_social_links.get("github") == "https://github.com/codecrews-test"

    # Save a second time
    data["hero_headline"] = "Second Updated Headline"
    resp2 = logged_in_client.post("/admin/settings", data=data, follow_redirects=True)
    assert resp2.status_code == 200

    with app.app_context():
        assert SiteSettings.query.count() == 1
        settings = SiteSettings.query.get(1)
        assert settings.hero_headline == "Second Updated Headline"


def test_stats_override_changes_home_counters_and_unset_restores_live(app, client, logged_in_client):
    # 1. Enable override
    data_override = {
        "override_stats": "y",
        "stats_groups": 42,
        "stats_members": 99,
        "stats_projects": 77,
    }
    resp = logged_in_client.post("/admin/settings", data=data_override, follow_redirects=True)
    assert resp.status_code == 200

    # Verify home page displays override counts
    home_resp = client.get("/")
    assert home_resp.status_code == 200
    assert b'data-number="42"' in home_resp.data
    assert b'data-number="99"' in home_resp.data
    assert b'data-number="77"' in home_resp.data

    # 2. Disable override (unchecked)
    data_live = {
        "hero_headline": "Back to live counters",
    }
    resp_unset = logged_in_client.post("/admin/settings", data=data_live, follow_redirects=True)
    assert resp_unset.status_code == 200

    # Live counts should be 0 because no groups/members/projects exist in clean test DB
    home_live_resp = client.get("/")
    assert home_live_resp.status_code == 200
    assert b'data-number="0"' in home_live_resp.data


def test_hero_image_requires_alt(app, logged_in_client):
    # Upload an image file without providing corresponding alt description
    image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00" + b"\x00" * 200
    data = {
        "hero_images": (io.BytesIO(image_bytes), "test_hero.jpg"),
        "hero_image_alts": "",  # Empty alt description
    }
    resp = logged_in_client.post(
        "/admin/settings",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    # Form validation should fail
    assert resp.status_code == 200
    assert b"Describe every hero image you upload." in resp.data

    with app.app_context():
        settings = SiteSettings.query.get(1)
        if settings:
            assert len(settings.hero_images) == 0


def test_footer_social_links_render_with_aria_labels(app, client, logged_in_client):
    # 1. With no settings, Follow column renders no empty list
    resp_empty = client.get("/")
    assert resp_empty.status_code == 200
    assert b'class="ftco-footer-social' not in resp_empty.data

    # 2. Configure github and twitter
    data = {
        "github_url": "https://github.com/codecrews",
        "twitter_url": "https://twitter.com/codecrews",
    }
    logged_in_client.post("/admin/settings", data=data, follow_redirects=True)

    resp_social = client.get("/")
    assert resp_social.status_code == 200
    assert b'aria-label="GitHub"' in resp_social.data
    assert b'aria-label="Twitter"' in resp_social.data
    assert b'https://github.com/codecrews' in resp_social.data
    assert b'https://twitter.com/codecrews' in resp_social.data


def test_seo_defaults_used_when_page_has_none(app, client, logged_in_client):
    data = {
        "seo_default_title": "Unique Custom Default Title",
        "seo_default_description": "Unique Custom Default Description for Testing",
    }
    logged_in_client.post("/admin/settings", data=data, follow_redirects=True)

    resp = client.get("/groups")
    assert resp.status_code == 200
    # Groups directory inherits default SEO description
    assert b"Unique Custom Default Description for Testing" in resp.data
