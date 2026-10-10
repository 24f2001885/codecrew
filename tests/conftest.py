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


@pytest.fixture
def coder_user(app, admin_user):
    with app.app_context():
        from app.models.group import Group
        from app.models.member import Member
        from app.models.coder_user import CoderUser

        group = Group(name="Alpha Crew", slug="alpha-crew")
        db.session.add(group)
        db.session.flush()

        member = Member(name="Coder Dev", group_id=group.id, role="Fullstack Dev")
        db.session.add(member)
        db.session.flush()

        coder = CoderUser(
            member_id=member.id,
            username="coderdev",
            email="coder@example.com",
            status="active",
            created_by_admin_id=admin_user.id,
        )
        coder.set_password("CoderPass1234!")
        db.session.add(coder)
        db.session.commit()
        db.session.refresh(coder)
        return coder


@pytest.fixture
def logged_in_coder_client(app, coder_user):
    c = app.test_client()
    resp = c.post(
        "/coder/login",
        data={"username": "coderdev", "password": "CoderPass1234!"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    return c
