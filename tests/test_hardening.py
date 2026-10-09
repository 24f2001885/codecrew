import io
from app import create_app
from app.extensions import db
from app.models.group import Group
from app.config import ProdConfig


def test_login_rate_limit(app):
    app.config["RATELIMIT_ENABLED"] = True
    client = app.test_client()

    # The 1st through 10th admin login attempts
    for i in range(10):
        resp = client.post("/admin/login", data={"username": "wronguser", "password": "wrongpassword"})
        assert resp.status_code == 200, f"Attempt {i+1} should return 200"

    # The 11th admin login attempt in a minute returns 429
    resp_11th = client.post("/admin/login", data={"username": "wronguser", "password": "wrongpassword"})
    assert resp_11th.status_code == 429
    assert b"Too Many Requests" in resp_11th.data


def test_public_form_rate_limits_hold(app):
    app.config["RATELIMIT_ENABLED"] = True
    client = app.test_client()

    with app.app_context():
        g = Group(name="Limit Squad", slug="limit-squad")
        db.session.add(g)
        db.session.commit()

    # /request-project is limited to 5 per hour
    for _ in range(5):
        resp = client.post(
            "/request-project",
            data={
                "name": "Limit Tester",
                "email": "limiter@example.com",
                "organization": "Limit Org",
                "project_summary": "Testing rate limit threshold for public requests.",
                "timeline_budget": "1 month",
            },
        )
        assert resp.status_code != 429

    # 6th attempt should be blocked
    resp_req_limit = client.post(
        "/request-project",
        data={
            "name": "Limit Tester",
            "email": "limiter@example.com",
            "organization": "Limit Org",
            "project_summary": "Testing rate limit threshold for public requests.",
            "timeline_budget": "1 month",
        },
    )
    assert resp_req_limit.status_code == 429

    # /group/<slug>/contact is limited to 5 per hour
    for _ in range(5):
        resp = client.post(
            "/group/limit-squad/contact",
            data={
                "name": "Limit Tester",
                "email": "limiter@example.com",
                "message": "Testing rate limit on group contact form.",
            },
        )
        assert resp.status_code != 429

    resp_contact_limit = client.post(
        "/group/limit-squad/contact",
        data={
            "name": "Limit Tester",
            "email": "limiter@example.com",
            "message": "Testing rate limit on group contact form.",
        },
    )
    assert resp_contact_limit.status_code == 429


def test_oversized_request_returns_friendly_redirect(app, client):
    # 5.5 MB payload exceeding the 5 MB MAX_CONTENT_LENGTH limit
    huge_data = b"A" * (5 * 1024 * 1024 + 500 * 1024)
    resp = client.post(
        "/request-project",
        data={"attachment": (io.BytesIO(huge_data), "huge_test_doc.pdf")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 302
    redirect_target = resp.headers.get("Location")
    follow_resp = client.get(redirect_target)
    assert b"That file is larger than 5 MB." in follow_resp.data


def test_disguised_upload_rejected_on_every_upload_endpoint(app, logged_in_client):
    # Disguised PHP script with a .png extension
    fake_png = b"<?php echo 'malicious payload'; ?>"

    # 1. Group creation endpoint
    resp_group = logged_in_client.post(
        "/admin/groups/new",
        data={
            "name": "Disguised Collective",
            "tagline": "Malicious upload test",
            "description": "Testing that disguised headers are trapped.",
            "logo": (io.BytesIO(fake_png), "malicious.png"),
        },
        content_type="multipart/form-data",
    )
    assert resp_group.status_code == 200
    assert b"Corrupted or invalid image file header." in resp_group.data or b"danger" in resp_group.data

    # 2. Member creation endpoint
    with app.app_context():
        group = Group(name="Disguise Container", slug="disguise-container")
        db.session.add(group)
        db.session.commit()
        gid = group.id

    resp_member = logged_in_client.post(
        f"/admin/groups/{gid}/members/new",
        data={
            "name": "Disguised Person",
            "role": "Hacker",
            "photo": (io.BytesIO(fake_png), "avatar.png"),
        },
        content_type="multipart/form-data",
    )

    assert resp_member.status_code == 200
    assert b"Corrupted or invalid image file header." in resp_member.data or b"danger" in resp_member.data



def test_private_folder_not_served_by_static_route(client):
    resp1 = client.get("/static/../instance/private_uploads/test.pdf")
    assert resp1.status_code in (400, 404)

    resp2 = client.get("/static/private_uploads/test.pdf")
    assert resp2.status_code in (400, 404)


def test_cookies_httponly_and_samesite_lax(app):
    prod_cfg = ProdConfig()
    assert prod_cfg.SESSION_COOKIE_SECURE is True
    assert prod_cfg.SESSION_COOKIE_HTTPONLY is True
    assert prod_cfg.SESSION_COOKIE_SAMESITE == "Lax"


def test_csrf_required_when_enabled():
    csrf_app = create_app("testing")
    csrf_app.config["WTF_CSRF_ENABLED"] = True

    with csrf_app.app_context():
        db.create_all()
        g = Group(name="Security Group", slug="security-group")
        db.session.add(g)
        db.session.commit()

        client = csrf_app.test_client()

        # Public form POST without CSRF token is rejected with 400 Bad Request
        resp_public = client.post(
            "/group/security-group/contact",
            data={"name": "Alice", "email": "alice@example.com", "message": "Test CSRF"},
        )
        assert resp_public.status_code == 400

        # Admin login POST without CSRF token is rejected with 400 Bad Request
        resp_admin = client.post(
            "/admin/login",
            data={"username": "admin", "password": "password"},
        )
        assert resp_admin.status_code == 400

        db.session.remove()
        db.drop_all()
