import pytest
from app import create_app
from app.extensions import db
from app.models.admin_user import AdminUser


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = AdminUser(username="testadmin")
        admin.set_password("AdminPass1234!")
        db.session.add(admin)
        db.session.commit()
        # Refresh inside context
        db.session.refresh(admin)
        return admin


@pytest.fixture
def logged_in_client(app, admin_user):
    c = app.test_client()
    resp = c.post(
        "/admin/login",
        data={"username": "testadmin", "password": "AdminPass1234!"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    return c
