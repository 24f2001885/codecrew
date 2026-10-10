from datetime import datetime
import pytest
from app.extensions import db, mail
from app.models.coder_application import CoderApplication
from app.models.project_request import ProjectRequest
from app.models.domain_alert import DomainAlert
from app.models.domain_alert_delivery import DomainAlertDelivery
from app.models.site_settings import SiteSettings
from app.services.alerts import (
    normalize_tags,
    get_request_tokens,
    get_application_tokens,
    find_matching_applications,
    send_alert_batch,
    format_default_summary,
)
from app.services.tokens import make_token


def test_tag_normalization_and_tokens():
    raw = " React ,  nodeJS  ,, Python , react "
    normalized = normalize_tags(raw)
    assert normalized == ["react", "nodejs", "python"]

    class FakeRequest:
        domain_tags = ["fintech", "Machine Learning"]
        project_type = "web_app"

    tokens = get_request_tokens(FakeRequest())
    assert "fintech" in tokens
    assert "machine learning" in tokens
    assert "web_app" in tokens


def test_matching_applications_eligibility(app):
    with app.app_context():
        req = ProjectRequest(
            name="Confidential Client Corp",
            email="secret.client@example.com",
            company="Secret Enterprise",
            project_type="web_app",
            budget_range="$20,000 - $50,000",
            timeline="3 months",
            description="Confidential high-frequency trading platform.",
            domain_tags=["fintech", "high_concurrency"],
        )
        db.session.add(req)
        db.session.flush()

        # 1. Eligible matching applicant
        app_eligible = CoderApplication(
            name="Eligible Match",
            email="eligible@example.com",
            project_types=["web_app"],
            domain_tags=["fintech"],
            alerts_consent=True,
            email_verified_at=datetime.utcnow(),
            status="pending",
        )
        # 2. Unverified applicant (must be excluded)
        app_unverified = CoderApplication(
            name="Unverified Match",
            email="unverified@example.com",
            project_types=["web_app"],
            domain_tags=["fintech"],
            alerts_consent=True,
            email_verified_at=None,
            status="pending",
        )
        # 3. Unsubscribed applicant (must be excluded)
        app_unsubscribed = CoderApplication(
            name="Unsubscribed Match",
            email="unsub@example.com",
            project_types=["web_app"],
            domain_tags=["fintech"],
            alerts_consent=True,
            email_verified_at=datetime.utcnow(),
            unsubscribed_at=datetime.utcnow(),
            status="pending",
        )
        # 4. Rejected applicant (must be excluded)
        app_rejected = CoderApplication(
            name="Rejected Match",
            email="rejected@example.com",
            project_types=["web_app"],
            domain_tags=["fintech"],
            alerts_consent=True,
            email_verified_at=datetime.utcnow(),
            status="rejected",
        )
        # 5. Non-matching applicant (must be excluded)
        app_non_match = CoderApplication(
            name="Other Domain",
            email="other@example.com",
            project_types=["mobile_app"],
            domain_tags=["ios"],
            alerts_consent=True,
            email_verified_at=datetime.utcnow(),
            status="pending",
        )

        db.session.add_all([app_eligible, app_unverified, app_unsubscribed, app_rejected, app_non_match])
        db.session.commit()

        matches = find_matching_applications(req)
        match_emails = [m.email for m in matches]

        assert "eligible@example.com" in match_emails
        assert "unverified@example.com" not in match_emails
        assert "unsub@example.com" not in match_emails
        assert "rejected@example.com" not in match_emails
        assert "other@example.com" not in match_emails


def test_privacy_invariant_alert_email_body(app, client):
    """
    Asserts alert email body contains summary and links ONLY.
    Must never contain requester name, email, company, description, budget, or request URL.
    """
    SENTINEL_NAME = "SuperSecretClientX"
    SENTINEL_EMAIL = "hidden.client.email@vault.example"
    SENTINEL_COMPANY = "TopSecretStealthCorp"
    SENTINEL_DESCRIPTION = "Proprietary algorithm description that must never leak."
    SENTINEL_BUDGET = "$999,999 budget tier"

    with app.app_context():
        req = ProjectRequest(
            name=SENTINEL_NAME,
            email=SENTINEL_EMAIL,
            company=SENTINEL_COMPANY,
            project_type="api_backend",
            description=SENTINEL_DESCRIPTION,
            budget_range=SENTINEL_BUDGET,
            domain_tags=["crypto", "distributed_systems"],
        )
        db.session.add(req)
        db.session.flush()

        applicant = CoderApplication(
            name="Crypto Engineer",
            email="crypto.dev@example.com",
            project_types=["api_backend"],
            domain_tags=["crypto"],
            alerts_consent=True,
            email_verified_at=datetime.utcnow(),
            status="pending",
        )
        db.session.add(applicant)
        db.session.commit()
        req_id = req.id

    with mail.record_messages() as outbox:
        with app.app_context():
            req_obj = db.session.get(ProjectRequest, req_id)
            summary = "New API / Backend project in distributed crypto."
            send_alert_batch(req_obj, summary=summary, is_auto=False)

        assert len(outbox) == 1
        msg = outbox[0]
        body = msg.body

        # Invariant checks: summary and action links are present
        assert "New API / Backend project in distributed crypto." in body
        assert "/join/interested/" in body
        assert "/join/unsubscribe/" in body

        # Strict secrecy checks: confidential requester data is completely absent
        assert SENTINEL_NAME not in body
        assert SENTINEL_EMAIL not in body
        assert SENTINEL_COMPANY not in body
        assert SENTINEL_DESCRIPTION not in body
        assert SENTINEL_BUDGET not in body
        assert f"/admin/project-requests/{req_id}" not in body
        assert f"/coder/opportunities/{req_id}" not in body

        # List-Unsubscribe headers present
        assert "List-Unsubscribe" in msg.extra_headers
        assert "List-Unsubscribe-Post" in msg.extra_headers


def test_interested_link_round_trip(app, client):
    with app.app_context():
        req = ProjectRequest(
            name="Client Name",
            email="client@example.com",
            project_type="web_app",
            description="Website project.",
        )
        db.session.add(req)
        db.session.flush()

        applicant = CoderApplication(
            name="Interested Dev",
            email="interested.dev@example.com",
            project_types=["web_app"],
            alerts_consent=True,
            email_verified_at=datetime.utcnow(),
            status="pending",
        )
        db.session.add(applicant)
        db.session.flush()

        alert = DomainAlert(
            project_request_id=req.id,
            summary="New web app project.",
            project_type_snapshot="web_app",
            recipient_count=1,
        )
        db.session.add(alert)
        db.session.flush()

        delivery = DomainAlertDelivery(
            alert_id=alert.id,
            application_id=applicant.id,
            status="sent",
        )
        db.session.add(delivery)
        db.session.commit()
        delivery_id = delivery.id

        token = make_token("alert-interest", {"delivery_id": delivery_id})

    # GET displays confirm page
    resp_get = client.get(f"/join/interested/{token}")
    assert resp_get.status_code == 200
    assert b"Confirm Your Interest" in resp_get.data

    # POST records interest
    resp_post = client.post(f"/join/interested/{token}", follow_redirects=True)
    assert resp_post.status_code == 200
    assert b"Interest Recorded!" in resp_post.data

    with app.app_context():
        updated_del = db.session.get(DomainAlertDelivery, delivery_id)
        assert updated_del.interested_at is not None


def test_batching_and_deduplication(app):
    with app.app_context():
        req = ProjectRequest(
            name="Batch Client",
            email="batch@example.com",
            project_type="desktop_software",
            description="Desktop tool.",
            domain_tags=["electron"],
        )
        db.session.add(req)
        db.session.flush()

        # Create 3 matching applicants
        for i in range(3):
            app_dev = CoderApplication(
                name=f"Desktop Dev {i}",
                email=f"desktop{i}@example.com",
                project_types=["desktop_software"],
                alerts_consent=True,
                email_verified_at=datetime.utcnow(),
                status="pending",
            )
            db.session.add(app_dev)
        db.session.commit()

        # Send batch with size 2
        req_obj = db.session.get(ProjectRequest, req.id)
        result1 = send_alert_batch(req_obj, summary="Batch 1 summary", batch_size=2)
        assert result1["sent"] == 2
        assert result1["remaining"] == 1

        # Second batch should send to the 1 remaining applicant without duplicating previous 2
        result2 = send_alert_batch(req_obj, summary="Batch 2 summary", batch_size=2)
        assert result2["sent"] == 1
        assert result2["remaining"] == 0

        # Third batch finds 0
        result3 = send_alert_batch(req_obj, summary="Batch 3 summary", batch_size=2)
        assert result3["sent"] == 0
        assert result3["remaining"] == 0


def test_auto_send_domain_alerts_on_request_creation(app, client):
    with app.app_context():
        settings = SiteSettings.get_settings()
        settings.auto_send_domain_alerts = True
        db.session.commit()

        applicant = CoderApplication(
            name="Auto Target",
            email="autotarget@example.com",
            project_types=["mobile_app"],
            alerts_consent=True,
            email_verified_at=datetime.utcnow(),
            status="pending",
        )
        db.session.add(applicant)
        db.session.commit()

    with mail.record_messages() as outbox:
        resp = client.post(
            "/request-project",
            data={
                "name": "Auto Requester",
                "email": "autoreq@example.com",
                "project_type": "mobile_app",
                "description": "Need an iOS and Android mobile app.",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302

        # 1 email to admin (notification) + 1 email to matching applicant (domain alert)
        recipients = [m.recipients[0] for m in outbox]
        assert "autotarget@example.com" in recipients

    with app.app_context():
        # Verify DomainAlert was recorded with is_auto=True
        alert = DomainAlert.query.filter_by(is_auto=True).first()
        assert alert is not None
        assert alert.project_type_snapshot == "mobile_app"

        # Restore setting
        settings = SiteSettings.get_settings()
        settings.auto_send_domain_alerts = False
        db.session.commit()
