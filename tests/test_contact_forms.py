import pytest
from app.models.group import Group
from app.models.contact_message import ContactMessage
from app.extensions import db, mail


@pytest.fixture
def contact_group(app):
    with app.app_context():
        g = Group(name="Frontend Wizards", slug="frontend-wizards")
        db.session.add(g)
        db.session.commit()
        return g.slug, g.id


def test_contact_valid_creates_message_and_mail(client, app, contact_group):
    slug, gid = contact_group
    data = {
        "name": "Alice Inquirer",
        "email": "alice@example.com",
        "subject": "Web App Proposal",
        "message": "We would like to hire your team for a project.",
        "website": "",
    }

    with mail.record_messages() as outbox:
        resp = client.post(f"/group/{slug}/contact", data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Thanks" in resp.data

        with app.app_context():
            msg = ContactMessage.query.filter_by(email="alice@example.com").first()
            assert msg is not None
            assert msg.group_id == gid
            assert msg.name == "Alice Inquirer"
            assert msg.subject == "Web App Proposal"
            assert msg.is_read is False

        assert len(outbox) == 1
        assert "New Contact Message" in outbox[0].subject


def test_contact_invalid_email_shows_inline_error(client, app, contact_group):
    slug, gid = contact_group
    data = {
        "name": "Bad Email User",
        "email": "not-a-valid-email",
        "message": "Valid message length here for testing.",
    }
    resp = client.post(f"/group/{slug}/contact", data=data)
    assert resp.status_code == 200
    assert b"valid email" in resp.data.lower() or b"error" in resp.data.lower()

    with app.app_context():
        assert ContactMessage.query.filter_by(name="Bad Email User").first() is None


def test_contact_honeypot_silent_success(client, app, contact_group):
    slug, gid = contact_group
    data = {
        "name": "Spam Bot",
        "email": "bot@spam.com",
        "message": "Buy cheap watches at our site right now!",
        "website": "http://spamsite.example.com",  # Honeypot filled!
    }
    resp = client.post(f"/group/{slug}/contact", data=data, follow_redirects=True)
    assert resp.status_code == 200
    # User sees thank you message so bot doesn't know it was blocked
    assert b"Thanks" in resp.data

    with app.app_context():
        assert ContactMessage.query.filter_by(name="Spam Bot").first() is None


def test_contact_mail_failure_keeps_row(client, app, contact_group, monkeypatch):
    slug, gid = contact_group

    def broken_send(msg):
        raise RuntimeError("SMTP Connection refused")

    monkeypatch.setattr(mail, "send", broken_send)

    data = {
        "name": "Resilient Inquirer",
        "email": "resilient@example.com",
        "subject": "Resilience test",
        "message": "Testing that mail errors do not crash form submission.",
    }
    resp = client.post(f"/group/{slug}/contact", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Thanks" in resp.data

    with app.app_context():
        msg = ContactMessage.query.filter_by(email="resilient@example.com").first()
        assert msg is not None


def test_contact_get_is_405(client, contact_group):
    slug, _ = contact_group
    resp = client.get(f"/group/{slug}/contact")
    assert resp.status_code == 405


def test_admin_messages_inbox_requires_login(client):
    resp = client.get("/admin/messages")
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_admin_messages_inbox_lists_message(logged_in_client, app, contact_group):
    slug, gid = contact_group
    # Seed a message
    with app.app_context():
        m = ContactMessage(
            group_id=gid,
            name="Bob Customer",
            email="bob@customer.com",
            subject="Looking for frontend",
            message="Need design help.",
        )
        db.session.add(m)
        db.session.commit()

    # Logged-in admin
    auth_resp = logged_in_client.get("/admin/messages")
    assert auth_resp.status_code == 200
    assert b"Bob Customer" in auth_resp.data
    assert b"Frontend Wizards" in auth_resp.data
    assert b"Messages" in auth_resp.data


def test_mark_read_and_delete_via_post_only(logged_in_client, app, contact_group):
    slug, gid = contact_group
    with app.app_context():
        m = ContactMessage(
            group_id=gid,
            name="Charlie",
            email="charlie@example.com",
            message="Test read toggle",
        )
        db.session.add(m)
        db.session.commit()
        mid = m.id

    # GET is 405
    assert logged_in_client.get(f"/admin/messages/{mid}/read").status_code == 405
    assert logged_in_client.get(f"/admin/messages/{mid}/delete").status_code == 405

    # POST toggles is_read to True
    resp_read = logged_in_client.post(f"/admin/messages/{mid}/read", follow_redirects=True)
    assert resp_read.status_code == 200
    with app.app_context():
        assert db.session.get(ContactMessage, mid).is_read is True

    # POST delete removes row
    resp_del = logged_in_client.post(f"/admin/messages/{mid}/delete", follow_redirects=True)
    assert resp_del.status_code == 200
    with app.app_context():
        assert db.session.get(ContactMessage, mid) is None


def test_message_always_has_group_id(app):
    with app.app_context():
        with pytest.raises(Exception):
            m = ContactMessage(
                group_id=None,
                name="Orphan",
                email="orphan@example.com",
                message="No group id provided",
            )
            db.session.add(m)
            db.session.commit()
