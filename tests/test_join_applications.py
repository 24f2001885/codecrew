import io
import pytest
from app.extensions import db, mail
from app.models.coder_application import CoderApplication
from app.models.site_settings import SiteSettings
from app.models.group import Group
from app.models.member import Member
from app.models.coder_user import CoderUser
from app.services.tokens import make_token


def test_join_page_renders_form(client):
    resp = client.get("/join")
    assert resp.status_code == 200
    assert b"Join as a Coder" in resp.data
    assert b"Domains of Interest" in resp.data
    assert b"Specialized Skills" in resp.data
    assert b"Submit Application" in resp.data


def test_join_closed_when_setting_disabled(app, client):
    with app.app_context():
        settings = SiteSettings.get_settings()
        settings.coder_applications_open = False
        db.session.commit()

    resp = client.get("/join")
    assert resp.status_code in [200, 404]
    assert b"Applications Closed" in resp.data

    with app.app_context():
        settings = SiteSettings.get_settings()
        settings.coder_applications_open = True
        db.session.commit()


def test_submit_application_validation_and_honeypot(app, client):
    # Honeypot: silently dropped without DB insertion
    resp_spam = client.post(
        "/join",
        data={
            "name": "Bot Name",
            "email": "bot@example.com",
            "honeypot": "spam content",
            "alerts_consent": "y",
            "project_types": ["web_app"],
        },
        follow_redirects=False,
    )
    assert resp_spam.status_code == 302
    with app.app_context():
        assert CoderApplication.query.filter_by(email="bot@example.com").first() is None

    # Missing consent: form re-renders with validation error
    resp_no_consent = client.post(
        "/join",
        data={
            "name": "Honest Dev",
            "email": "dev@example.com",
            "project_types": ["web_app"],
            # alerts_consent missing
        },
        follow_redirects=True,
    )
    assert b"You must consent" in resp_no_consent.data

    # Missing project types: form re-renders
    resp_no_types = client.post(
        "/join",
        data={
            "name": "Honest Dev",
            "email": "dev@example.com",
            "alerts_consent": "y",
        },
        follow_redirects=True,
    )
    assert b"Please select at least one domain" in resp_no_types.data


def test_submit_valid_application_creates_row_and_sends_verification_email(app, client):
    with mail.record_messages() as outbox:
        resp = client.post(
            "/join",
            data={
                "name": "Jane Developer",
                "email": "jane@example.com",
                "project_types": ["web_app", "api_backend"],
                "domain_tags": "react, flask, postgresql",
                "headline": "Fullstack Python Engineer",
                "portfolio_url": "https://janedev.example",
                "message": "Excited to collaborate on web projects.",
                "alerts_consent": "y",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/join/thanks" in resp.headers["Location"]

        # Assert email sent
        assert len(outbox) == 1
        assert "Verify Your Email" in outbox[0].subject
        assert "jane@example.com" in outbox[0].recipients
        assert "/join/verify/" in outbox[0].body

    with app.app_context():
        app_record = CoderApplication.query.filter_by(email="jane@example.com").first()
        assert app_record is not None
        assert app_record.name == "Jane Developer"
        assert "web_app" in app_record.project_types
        assert "react" in app_record.domain_tags
        assert app_record.status == "pending"
        assert app_record.email_verified_at is None
        assert app_record.alerts_consent is True


def test_verify_email_flow(app, client):
    with app.app_context():
        app_record = CoderApplication(
            name="Verify Tester",
            email="verifytest@example.com",
            project_types=["mobile_app"],
            domain_tags=["ios", "swift"],
            alerts_consent=True,
            status="pending",
        )
        db.session.add(app_record)
        db.session.commit()
        app_id = app_record.id

        token = make_token("app-verify", {"id": app_id})

    with mail.record_messages() as outbox:
        resp = client.get(f"/join/verify/{token}")
        assert resp.status_code == 200
        assert b"Email Verified!" in resp.data

        # Admin notified of verified application
        assert len(outbox) == 1
        assert "New Verified Coder Application" in outbox[0].subject

    with app.app_context():
        updated = db.session.get(CoderApplication, app_id)
        assert updated.email_verified_at is not None

    # Invalid token returns 400 error page
    resp_bad = client.get("/join/verify/invalid-token-signature")
    assert resp_bad.status_code == 400
    assert b"Link Invalid or Expired" in resp_bad.data


def test_unsubscribe_email_flow(app, client):
    with app.app_context():
        app_record = CoderApplication(
            name="Unsub Tester",
            email="unsubtest@example.com",
            project_types=["web_app"],
            alerts_consent=True,
            status="pending",
        )
        db.session.add(app_record)
        db.session.commit()
        app_id = app_record.id

        token = make_token("app-unsub", {"id": app_id})

    resp = client.get(f"/join/unsubscribe/{token}")
    assert resp.status_code == 200
    assert b"You Have Been Unsubscribed" in resp.data

    with app.app_context():
        updated = db.session.get(CoderApplication, app_id)
        assert updated.unsubscribed_at is not None


def test_reapply_with_same_email_updates_existing_record(app, client):
    # First submission
    client.post(
        "/join",
        data={
            "name": "Repeat Dev",
            "email": "repeat@example.com",
            "project_types": ["web_app"],
            "domain_tags": "vue",
            "headline": "Vue Dev",
            "alerts_consent": "y",
        },
    )

    # Second submission with updated fields
    client.post(
        "/join",
        data={
            "name": "Repeat Dev Senior",
            "email": "repeat@example.com",
            "project_types": ["web_app", "mobile_app"],
            "domain_tags": "vue, nuxt, flutter",
            "headline": "Senior Fullstack Dev",
            "alerts_consent": "y",
        },
    )

    with app.app_context():
        all_recs = CoderApplication.query.filter_by(email="repeat@example.com").all()
        assert len(all_recs) == 1
        assert all_recs[0].name == "Repeat Dev Senior"
        assert "flutter" in all_recs[0].domain_tags
        assert "mobile_app" in all_recs[0].project_types


def test_admin_applications_crud_and_conversion(app, logged_in_client):
    with app.app_context():
        group = Group(name="Alpha Crew", slug="alpha-crew")
        db.session.add(group)
        db.session.flush()

        app_rec = CoderApplication(
            name="Applicant To Convert",
            email="applicant.convert@example.com",
            project_types=["web_app"],
            domain_tags=["django", "react"],
            alerts_consent=True,
            status="pending",
        )
        db.session.add(app_rec)
        db.session.commit()
        app_id = app_rec.id
        group_id = group.id

    # Admin visits inbox
    resp_inbox = logged_in_client.get("/admin/coder-applications")
    assert resp_inbox.status_code == 200
    assert b"Applicant To Convert" in resp_inbox.data

    # Admin visits detail
    resp_detail = logged_in_client.get(f"/admin/coder-applications/{app_id}")
    assert resp_detail.status_code == 200
    assert b"Applicant To Convert" in resp_detail.data

    # Admin approves
    resp_appr = logged_in_client.post(f"/admin/coder-applications/{app_id}/approve", follow_redirects=True)
    assert resp_appr.status_code == 200
    assert b"approved" in resp_appr.data.lower()

    # Admin converts
    with mail.record_messages() as outbox:
        resp_conv = logged_in_client.post(
            f"/admin/coder-applications/{app_id}/convert",
            data={
                "group_id": str(group_id),
                "member_name": "Applicant To Convert",
                "role": "Lead Architect",
                "username": "architectdev",
            },
            follow_redirects=True,
        )
        assert resp_conv.status_code == 200
        assert b"Converted" in resp_conv.data

        # Invite sent to applicant
        assert len(outbox) == 1
        assert "Welcome to CodeCrews" in outbox[0].subject
        assert "applicant.convert@example.com" in outbox[0].recipients

    with app.app_context():
        updated_app = db.session.get(CoderApplication, app_id)
        assert updated_app.status == "converted"
        assert updated_app.converted_coder_id is not None

        coder = db.session.get(CoderUser, updated_app.converted_coder_id)
        assert coder is not None
        assert coder.username == "architectdev"
        assert coder.status == "invited"

        member = coder.member
        assert member is not None
        assert member.name == "Applicant To Convert"
        assert member.role == "Lead Architect"
        assert member.group_id == group_id
