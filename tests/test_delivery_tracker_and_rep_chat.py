import pytest
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.coder_user import CoderUser
from app.models.project_request import ProjectRequest
from app.models.request_access_grant import RequestAccessGrant
from app.models.project_milestone import ProjectMilestone
from app.models.project_offer import ProjectOffer


def test_direct_squad_representative_chat_initiation(app, client, coder_user, admin_user):
    # Get coder's group slug
    with app.app_context():
        cu = db.session.get(CoderUser, coder_user.id)
        group_slug = cu.member.group.slug
        group_id = cu.member.group.id

    # Normal visitor initiates direct chat with squad representative
    resp = client.post(
        f"/group/{group_slug}/chat-representative",
        data={
            "name": "David Founder",
            "email": "david@fintech-startup.example",
            "project_type": "web_app",
            "budget_range": "$15,000 - $25,000",
            "message": "We need Acme Devs to build our cryptocurrency ledger MVP.",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Direct inquiry room created" in resp.data or b"David Founder" in resp.data

    with app.app_context():
        req = ProjectRequest.query.filter_by(email="david@fintech-startup.example").first()
        assert req is not None
        assert req.assigned_group_id == group_id
        # Check grant was created for coder
        grant = RequestAccessGrant.query.filter_by(project_request_id=req.id, coder_id=coder_user.id).first()
        assert grant is not None
        assert grant.is_active is True


def test_sprint_delivery_tracking_lifecycle(app, logged_in_coder_client, coder_user, admin_user, client):
    # Setup request and grant
    with app.app_context():
        cu = db.session.get(CoderUser, coder_user.id)
        req = ProjectRequest(
            name="Bob Enterprise",
            email="bob@enterprise.example",
            project_type="web_app",
            budget_range="$30,000",
            timeline="3 months",
            description="Enterprise resource planning platform.",
            status="assigned",
            assigned_group_id=cu.member.group.id,
        )
        db.session.add(req)
        db.session.flush()

        grant = RequestAccessGrant(
            project_request_id=req.id,
            coder_id=cu.id,
            scope="brief_and_contact",
            granted_by_admin_id=admin_user.id,
        )
        db.session.add(grant)
        db.session.commit()
        req_id = req.id

    # 1. Coder adds a milestone
    add_ms_resp = logged_in_coder_client.post(
        f"/coder/opportunities/{req_id}/milestones",
        data={
            "title": "Sprint 1: Architecture & RBAC",
            "description": "PostgreSQL relational schemas and JWT auth.",
            "deliverable_url": "https://github.com/example/erp-repo/pull/1",
        },
        follow_redirects=True,
    )
    assert add_ms_resp.status_code == 200
    assert b"Sprint 1: Architecture" in add_ms_resp.data

    with app.app_context():
        ms = ProjectMilestone.query.filter_by(project_request_id=req_id).first()
        assert ms is not None
        assert ms.status == "in_progress"
        ms_id = ms.id

    # 2. Coder submits deliverable for review
    submit_ms_resp = logged_in_coder_client.post(
        f"/coder/opportunities/{req_id}/milestones/{ms_id}/submit",
        data={
            "deliverable_url": "https://staging.erp.example/auth-demo",
            "deliverable_notes": "All authentication tests passing with 99% coverage.",
        },
        follow_redirects=True,
    )
    assert submit_ms_resp.status_code == 200
    assert b"submitted for client" in submit_ms_resp.data.lower()

    # 3. Client visits their project hub and sees submitted deliverable
    hub_resp = client.get(f"/request/{req_id}/hub")
    assert hub_resp.status_code == 200
    assert b"Sprint & Delivery Tracker" in hub_resp.data
    assert b"https://staging.erp.example/auth-demo" in hub_resp.data
    assert b"Review & Approve Milestone" in hub_resp.data

    # 4. Client approves milestone
    approve_resp = client.post(
        f"/request/{req_id}/hub/milestone/{ms_id}/approve",
        follow_redirects=True,
    )
    assert approve_resp.status_code == 200
    assert b"approved successfully" in approve_resp.data.lower()

    with app.app_context():
        updated_ms = db.session.get(ProjectMilestone, ms_id)
        assert updated_ms.status == "completed"
        updated_req = db.session.get(ProjectRequest, req_id)
        assert updated_req.progress_percentage == 100
        # Automatically transitions to completed when all milestones are done
        assert updated_req.status == "completed"
