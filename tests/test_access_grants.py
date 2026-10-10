from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.project_request import ProjectRequest
from app.models.request_access_grant import RequestAccessGrant
from app.models.coder_user import CoderUser
from app.services.access import (
    serialize_request_for_coder,
    get_granted_request_or_404,
    active_grants_query,
)


def test_grant_scope_sentinel_privacy_check(app, admin_user, coder_user):
    with app.app_context():
        sentinel_name = "SECRET_CLIENT_NAME_98765"
        sentinel_email = "confidential_client_98765@example.com"
        sentinel_company = "CLASSIFIED_CORP_98765"
        sentinel_notes = "SUPER_ADMIN_CONFIDENTIAL_INTERNAL_NOTE_98765"

        req = ProjectRequest(
            name=sentinel_name,
            email=sentinel_email,
            company=sentinel_company,
            project_type="web_app",
            budget_range="$10k-$20k",
            timeline="2 months",
            description="Build a high performance web portal.",
            internal_notes=sentinel_notes,
            domain_tags=["python", "react"],
        )
        db.session.add(req)
        db.session.flush()

        # Grant 1: brief_only
        grant_brief = RequestAccessGrant(
            project_request_id=req.id,
            coder_id=coder_user.id,
            scope="brief_only",
            granted_by_admin_id=admin_user.id,
        )
        db.session.add(grant_brief)
        db.session.commit()

        coder = db.session.get(CoderUser, coder_user.id)
        serialized = serialize_request_for_coder(req, grant_brief)

        # In brief_only: name, email, company must be None
        assert serialized["name"] is None
        assert serialized["email"] is None
        assert serialized["company"] is None
        assert "internal_notes" not in serialized
        assert serialized["project_type"] == "web_app"

        # Grant 2: brief_and_contact
        grant_brief.scope = "brief_and_contact"
        db.session.commit()

        serialized_contact = serialize_request_for_coder(req, grant_brief)
        assert serialized_contact["name"] == sentinel_name
        assert serialized_contact["email"] == sentinel_email
        assert serialized_contact["company"] == sentinel_company
        # In ALL scopes, internal_notes MUST NEVER appear
        assert "internal_notes" not in serialized_contact


def test_ungranted_or_expired_or_revoked_grant_returns_404(app, logged_in_coder_client, admin_user, coder_user):
    with app.app_context():
        req = ProjectRequest(
            name="Test Client",
            email="client@example.com",
            project_type="mobile_app",
            description="Mobile application for iOS and Android.",
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    # 1. Without any grant -> 404 (never 403)
    resp = logged_in_coder_client.get(f"/coder/opportunities/{req_id}")
    assert resp.status_code == 404

    # 2. With expired grant -> 404
    with app.app_context():
        grant = RequestAccessGrant(
            project_request_id=req_id,
            coder_id=coder_user.id,
            scope="brief_only",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            granted_by_admin_id=admin_user.id,
        )
        db.session.add(grant)
        db.session.commit()

    resp = logged_in_coder_client.get(f"/coder/opportunities/{req_id}")
    assert resp.status_code == 404

    # 3. With revoked grant -> 404
    with app.app_context():
        grant = RequestAccessGrant.query.filter_by(project_request_id=req_id, coder_id=coder_user.id).first()
        grant.expires_at = None
        grant.revoked_at = datetime.now(timezone.utc)
        grant.revoked_by_admin_id = admin_user.id
        db.session.commit()

    resp = logged_in_coder_client.get(f"/coder/opportunities/{req_id}")
    assert resp.status_code == 404

    # 4. With active grant -> 200
    with app.app_context():
        g = RequestAccessGrant.query.filter_by(project_request_id=req_id, coder_id=coder_user.id).first()
        g.revoked_at = None
        g.revoked_by_admin_id = None
        g.expires_at = None
        db.session.commit()

    resp = logged_in_coder_client.get(f"/coder/opportunities/{req_id}")
    assert resp.status_code == 200
    assert b"Mobile application for iOS and Android" in resp.data


def test_revoking_coder_revokes_all_active_grants(app, client, logged_in_client, admin_user, coder_user):
    with app.app_context():
        req = ProjectRequest(
            name="Client A",
            email="a@example.com",
            project_type="web_app",
            description="Web app project.",
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
        grant_id = grant.id

    # Admin revokes the coder via POST /admin/coders/<id>/revoke
    resp = logged_in_client.post(
        f"/admin/coders/{coder_user.id}/revoke",
        data={"revoke_reason": "Inactivity"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        coder = db.session.get(CoderUser, coder_user.id)
        assert coder.status == "revoked"
        assert coder.revoked_at is not None

        grant = db.session.get(RequestAccessGrant, grant_id)
        assert grant.revoked_at is not None
        assert not grant.is_active

        # Active grants query returns 0
        assert active_grants_query(coder.id).count() == 0
