from app.extensions import db
from app.models.coder_user import CoderUser
from app.models.project_request import ProjectRequest
from app.models.request_access_grant import RequestAccessGrant


def test_coder_cannot_access_admin_routes(app, logged_in_coder_client):
    # Coder authenticated session attempting to reach /admin/* routes should receive HTTP 403
    admin_paths = [
        "/admin/dashboard",
        "/admin/groups",
        "/admin/messages",
        "/admin/project-requests",
        "/admin/coders",
        "/admin/coder-applications",
        "/admin/audit-log",
        "/admin/settings",
    ]
    for path in admin_paths:
        resp = logged_in_coder_client.get(path)
        assert resp.status_code == 403, f"Coder accessed {path} with status {resp.status_code}"


def test_admin_cannot_access_coder_portal_routes(app, logged_in_client):
    # Admin authenticated session attempting to reach /coder/* protected routes should receive HTTP 403
    coder_paths = [
        "/coder/dashboard",
        "/coder/profile",
        "/coder/projects",
        "/coder/opportunities",
    ]
    for path in coder_paths:
        resp = logged_in_client.get(path)
        assert resp.status_code == 403, f"Admin accessed {path} with status {resp.status_code}"


def test_anonymous_redirects_to_login(app, client):
    # Anonymous visiting /admin/* redirects to /admin/login
    admin_resp = client.get("/admin/dashboard", follow_redirects=False)
    assert admin_resp.status_code == 302
    assert "/admin/login" in admin_resp.headers["Location"]

    # Anonymous visiting /coder/* redirects to /coder/login
    coder_resp = client.get("/coder/dashboard", follow_redirects=False)
    assert coder_resp.status_code == 302
    assert "/coder/login" in coder_resp.headers["Location"]


def test_revoked_coder_session_invalidated_immediately(app, client, coder_user):
    # Log in as coder
    login_resp = client.post(
        "/coder/login",
        data={"username": "coderdev", "password": "CoderPass1234!"},
        follow_redirects=False,
    )
    assert login_resp.status_code == 302

    # Verify session is currently active
    resp1 = client.get("/coder/dashboard")
    assert resp1.status_code == 200

    # Admin revokes the coder in DB
    coder = db.session.get(CoderUser, coder_user.id)
    coder.status = "revoked"
    db.session.commit()

    # Next request by this coder in the same session must be rejected (load_user returns None -> redirects to login)
    resp2 = client.get("/coder/dashboard", follow_redirects=False)
    assert resp2.status_code == 302
    assert "/coder/login" in resp2.headers["Location"]


def test_reinstated_coder_sees_zero_opportunities(app, client, admin_user, coder_user):
    with app.app_context():
        # Create request and grant
        req = ProjectRequest(
            name="Confidential Client",
            email="client@example.com",
            project_type="web_app",
            description="Opportunity description.",
        )
        db.session.add(req)
        db.session.flush()

        grant = RequestAccessGrant(
            project_request_id=req.id,
            coder_id=coder_user.id,
            scope="brief_only",
            granted_by_admin_id=admin_user.id,
        )
        db.session.add(grant)
        db.session.commit()

        # Admin revokes coder
        from app.routes.admin import coder_revoke, coder_reinstate
        coder = db.session.get(CoderUser, coder_user.id)
        coder.status = "revoked"
        grant.revoked_at = db.func.now()
        db.session.commit()

        # Admin reinstates coder
        coder.status = "active"
        db.session.commit()

    # Log in as reinstated coder
    c = app.test_client()
    c.post("/coder/login", data={"username": "coderdev", "password": "CoderPass1234!"})

    # Coder sees zero opportunities
    opp_resp = c.get("/coder/opportunities")
    assert opp_resp.status_code == 200
    assert b"No Active Opportunities" in opp_resp.data


def test_private_files_not_retrievable_under_static(app, client):
    # Ensure confidential private requests cannot be reached via /static/
    resp = client.get("/static/uploads/requests/confidential.pdf")
    assert resp.status_code in [404, 302]

    resp_app = client.get("/static/uploads/applications/resume.pdf")
    assert resp_app.status_code in [404, 302]
