import pytest
from app.extensions import db
from app.models.admin_user import AdminUser
from app.models.coder_user import CoderUser
from app.models.group import Group
from app.models.member import Member
from app.services.sample_data import create_sample_data, create_sample_coder


def test_create_sample_coder_and_login_flow(app, client):
    with app.app_context():
        # Setup admin and sample data
        admin = AdminUser(username="seedadmin")
        admin.set_password("AdminPass1234!")
        db.session.add(admin)
        db.session.commit()

        create_sample_data()
        coder = create_sample_coder(admin=admin, username="testcoder", password="CoderPass123!", email="testcoder@example.com")
        assert coder is not None
        assert coder.username == "testcoder"
        assert coder.status == "active"
        assert coder.is_active is True
        assert coder.check_password("CoderPass123!") is True
        assert coder.member is not None

        # Verify idempotency
        coder_again = create_sample_coder(admin=admin, username="testcoder", password="CoderPass123!", email="testcoder@example.com")
        assert coder_again.id == coder.id
        assert CoderUser.query.filter_by(username="testcoder").count() == 1

    # Test login with seeded coder credentials
    login_resp = client.post(
        "/coder/login",
        data={"username": "testcoder", "password": "CoderPass123!"},
        follow_redirects=True,
    )
    assert login_resp.status_code == 200
    assert b"Welcome back, testcoder!" in login_resp.data

    # Test coder views
    dash_resp = client.get("/coder/dashboard")
    assert dash_resp.status_code == 200
    assert b"Coder Portal" in dash_resp.data
    assert b"Acme Devs" in dash_resp.data

    opps_resp = client.get("/coder/opportunities")
    assert opps_resp.status_code == 200
    assert b"Opportunities" in opps_resp.data

    proj_resp = client.get("/coder/projects")
    assert proj_resp.status_code == 200
    assert b"Group Projects" in proj_resp.data

    prof_resp = client.get("/coder/profile")
    assert prof_resp.status_code == 200
    assert b"Alex Vance" in prof_resp.data
