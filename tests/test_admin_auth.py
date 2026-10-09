from app.models.admin_user import AdminUser
from app.services.tokens import make_token, fingerprint


def test_login_page_renders(client):
    resp = client.get("/admin/login")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'name="username"' in html
    assert 'name="password"' in html
    assert 'type="submit"' in html


def test_login_successful(client, admin_user):
    resp = client.post(
        "/admin/login",
        data={"username": "testadmin", "password": "AdminPass1234!"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Welcome back, Super Admin!" in html


def test_login_invalid_password(client, admin_user):
    resp = client.post(
        "/admin/login",
        data={"username": "testadmin", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Invalid username or password" in html


def test_logout(logged_in_client):
    resp = logged_in_client.post("/admin/logout", follow_redirects=True)
    assert resp.status_code == 200
    # Next dashboard request should redirect to login
    dash_resp = logged_in_client.get("/admin/dashboard", follow_redirects=False)
    assert dash_resp.status_code == 302
    assert "/admin/login" in dash_resp.headers["Location"]


def test_forgot_password_generic_response(client, admin_user):
    resp = client.post(
        "/admin/forgot-password",
        data={"username": "testadmin"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "If that account exists, a reset link has been sent" in html


def test_reset_password_minimum_length_rejected(client, admin_user):
    with client.application.app_context():
        tok = make_token("admin_reset", {"id": admin_user.id, "fp": fingerprint(admin_user.password_hash)})

    # Password with 9 chars should be rejected
    resp = client.post(
        f"/admin/reset-password/{tok}",
        data={"password": "short9chr", "confirm_password": "short9chr"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "at least 10 characters" in html
