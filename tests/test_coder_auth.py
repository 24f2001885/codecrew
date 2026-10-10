import pytest
from app.extensions import db
from app.models.coder_user import CoderUser
from app.models.audit_log import AuditLog
from app.services.tokens import make_token, fingerprint


def test_coder_invite_acceptance(app, client, admin_user, coder_user):
    with app.app_context():
        # Set coder status to invited
        coder = db.session.get(CoderUser, coder_user.id)
        coder.status = "invited"
        coder.password_hash = None
        db.session.commit()

        token = make_token("coder_invite", {"id": coder.id})

    # GET accept-invite page
    resp = client.get(f"/coder/accept-invite/{token}")
    assert resp.status_code == 200
    assert b"Activate Your Coder Account" in resp.data

    # POST new password (minimum 10 chars)
    resp = client.post(
        f"/coder/accept-invite/{token}",
        data={
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Your account has been activated" in resp.data

    with app.app_context():
        updated_coder = db.session.get(CoderUser, coder_user.id)
        assert updated_coder.status == "active"
        assert updated_coder.activated_at is not None
        assert updated_coder.check_password("SecurePassword123!")

        # Audit log verification
        audit = AuditLog.query.filter_by(action="coder.invite_accepted", target_id=str(coder_user.id)).first()
        assert audit is not None


def test_coder_login_and_logout(app, client, coder_user):
    # Valid login
    resp = client.post(
        "/coder/login",
        data={
            "username": "coderdev",
            "password": "CoderPass1234!",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Welcome back, coderdev!" in resp.data

    # Access protected dashboard
    dash_resp = client.get("/coder/dashboard")
    assert dash_resp.status_code == 200

    # Logout
    logout_resp = client.post("/coder/logout", follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"You have been logged out" in logout_resp.data

    # Unauthenticated access now redirects to login
    redirect_resp = client.get("/coder/dashboard", follow_redirects=False)
    assert redirect_resp.status_code == 302
    assert "/coder/login" in redirect_resp.headers["Location"]


def test_revoked_coder_cannot_login(app, client, coder_user):
    with app.app_context():
        coder = db.session.get(CoderUser, coder_user.id)
        coder.status = "revoked"
        db.session.commit()

    resp = client.post(
        "/coder/login",
        data={
            "username": "coderdev",
            "password": "CoderPass1234!",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"revoked" in resp.data.lower()


def test_coder_forgot_and_reset_password(app, client, coder_user):
    # Request reset link
    resp = client.post(
        "/coder/forgot-password",
        data={"email": "coder@example.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"password reset instructions have been sent" in resp.data.lower()

    with app.app_context():
        coder = db.session.get(CoderUser, coder_user.id)
        fp = fingerprint(coder.password_hash)
        token = make_token("coder_reset", {"id": coder.id, "fp": fp})

    # Access reset link
    get_resp = client.get(f"/coder/reset-password/{token}")
    assert get_resp.status_code == 200

    # Reset password
    post_resp = client.post(
        f"/coder/reset-password/{token}",
        data={
            "password": "NewCoderPassword123!",
            "confirm_password": "NewCoderPassword123!",
        },
        follow_redirects=True,
    )
    assert post_resp.status_code == 200
    assert b"password has been reset successfully" in post_resp.data.lower()

    # Verify single-use token: reuse must fail
    reuse_resp = client.get(f"/coder/reset-password/{token}", follow_redirects=True)
    assert b"already been used" in reuse_resp.data.lower()
