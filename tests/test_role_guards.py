import pytest
from flask import Blueprint
from flask_login import UserMixin, login_user
from app.extensions import db
from app.security.decorators import super_admin_required
from app.services.tokens import make_token, read_token, fingerprint
from app.models.admin_user import AdminUser
from app.models import Group, Member, Project, BlogPost, ContactMessage, ProjectRequest, SiteSettings


def test_admin_session_id_is_namespaced(logged_in_client):
    """After login, session '_user_id' must start with 'admin:'."""
    with logged_in_client.session_transaction() as sess:
        assert "_user_id" in sess
        assert sess["_user_id"].startswith("admin:")


def test_dashboard_still_requires_login(client):
    """GET /admin/dashboard returns 302 redirecting to /admin/login."""
    resp = client.get("/admin/dashboard", follow_redirects=False)
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_wrong_role_gets_403(app):
    """A logged-in user whose role is 'coder' receives 403 on super_admin_required routes."""
    test_bp = Blueprint("test_guard_bp", __name__)

    @test_bp.route("/test-guarded")
    @super_admin_required
    def guarded_view():
        return "allowed"

    app.register_blueprint(test_bp)

    class FakeCoderUser(UserMixin):
        id = "coder-123"
        role = "coder"

        def get_id(self):
            return "coder:coder-123"

    with app.test_request_context():
        fake_user = FakeCoderUser()
        login_user(fake_user)
        # Call guarded_view directly or via test client with session
        with app.test_client() as tc:
            with tc.session_transaction() as sess:
                sess["_user_id"] = "coder:coder-123"
            resp = tc.get("/test-guarded")
            assert resp.status_code == 403


def test_tokens_round_trip_and_purpose_isolation(app):
    """Tokens read back with same purpose but are rejected when read with a different purpose."""
    with app.app_context():
        tok = make_token("admin_reset", {"id": "1", "data": "test"})
        read_back = read_token("admin_reset", tok)
        assert read_back == {"id": "1", "data": "test"}

        # Purpose isolation: reading with different salt returns None
        assert read_token("coder_reset", tok) is None
        assert read_token("admin_reset", "tampered-token") is None


def test_reset_token_single_use(client, admin_user):
    """A reset token can be used once; using it again is rejected because password hash changed."""
    with client.application.app_context():
        tok = make_token(
            "admin_reset",
            {"id": admin_user.id, "fp": fingerprint(admin_user.password_hash)},
        )

    # First reset succeeds
    resp1 = client.post(
        f"/admin/reset-password/{tok}",
        data={"password": "NewSecretPassword123!", "confirm_password": "NewSecretPassword123!"},
        follow_redirects=False,
    )
    assert resp1.status_code == 302
    assert "/admin/login" in resp1.headers["Location"]

    # Second reset with same token is rejected
    resp2 = client.post(
        f"/admin/reset-password/{tok}",
        data={"password": "AnotherSecret123!", "confirm_password": "AnotherSecret123!"},
        follow_redirects=False,
    )
    assert resp2.status_code == 302
    assert "/admin/forgot-password" in resp2.headers["Location"]


def test_all_models_registered(app):
    """All 8 core models are registered with the SQLAlchemy metadata."""
    tables = db.metadata.tables.keys()
    for expected_table in [
        "admin_users",
        "groups",
        "members",
        "projects",
        "blog_posts",
        "contact_messages",
        "project_requests",
        "site_settings",
    ]:
        assert expected_table in tables, f"Expected table '{expected_table}' not in metadata"
