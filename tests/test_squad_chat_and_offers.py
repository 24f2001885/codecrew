import pytest
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.coder_user import CoderUser
from app.models.project_request import ProjectRequest
from app.models.request_access_grant import RequestAccessGrant
from app.models.group_chat_message import GroupChatMessage
from app.models.project_offer import ProjectOffer
from app.models.project_discussion import ProjectDiscussionMessage


def test_squad_chat_room(app, logged_in_coder_client, coder_user):
    # GET chat room
    resp = logged_in_coder_client.get("/coder/chat")
    assert resp.status_code == 200
    assert b"Squad Room" in resp.data or b"Insider Channel" in resp.data

    # POST chat message
    post_resp = logged_in_coder_client.post(
        "/coder/chat",
        data={"content": "Let us deploy the Kubernetes cluster today!"},
        follow_redirects=True,
    )
    assert post_resp.status_code == 200
    assert b"Let us deploy the Kubernetes cluster today!" in post_resp.data

    # GET messages JSON API
    json_resp = logged_in_coder_client.get("/coder/chat/messages")
    assert json_resp.status_code == 200
    data = json_resp.get_json()
    assert "messages" in data
    assert any("Kubernetes" in m["content"] for m in data["messages"])


def test_squad_offer_submission_and_client_acceptance(app, logged_in_coder_client, coder_user, admin_user, client):
    with app.app_context():
        # Create a project request
        req = ProjectRequest(
            name="Alice Enterprise",
            email="alice@enterprise.example",
            project_type="web_app",
            budget_range="$20,000 - $30,000",
            timeline="2 months",
            description="High-security corporate procurement portal.",
            status="in_review",
        )
        db.session.add(req)
        db.session.flush()

        # Grant access to coder
        grant = RequestAccessGrant(
            project_request_id=req.id,
            coder_id=coder_user.id,
            scope="brief_and_contact",
            granted_by_admin_id=admin_user.id,
        )
        db.session.add(grant)
        db.session.commit()
        req_id = req.id

    # Coder submits offer
    offer_resp = logged_in_coder_client.post(
        f"/coder/opportunities/{req_id}/offer",
        data={
            "proposed_budget": "$22,000",
            "proposed_timeline": "7 weeks",
            "pitch": "Our squad has extensive experience building secure procurement workflows with role-based auth.",
            "deliverables": "Sprint 1: Architecture\nSprint 2: MVP APIs\nSprint 3: Security audit",
        },
        follow_redirects=True,
    )
    assert offer_resp.status_code == 200
    assert b"$22,000" in offer_resp.data
    assert b"7 weeks" in offer_resp.data

    # Coder posts in discussion
    coder_msg_resp = logged_in_coder_client.post(
        f"/coder/opportunities/{req_id}/discuss",
        data={"content": "We are ready to start sprint 1 whenever you are ready."},
        follow_redirects=True,
    )
    assert coder_msg_resp.status_code == 200
    assert b"ready to start sprint 1" in coder_msg_resp.data

    # Client visits their Project Hub
    hub_resp = client.get(f"/request/{req_id}/hub")
    assert hub_resp.status_code == 200
    assert b"Alice Enterprise" in hub_resp.data
    assert b"$22,000" in hub_resp.data
    assert b"7 weeks" in hub_resp.data
    assert b"ready to start sprint 1" in hub_resp.data

    with app.app_context():
        offer_obj = ProjectOffer.query.filter_by(project_request_id=req_id).first()
        assert offer_obj is not None
        offer_id = offer_obj.id

    # Client posts to discussion
    client_discuss_resp = client.post(
        f"/request/{req_id}/hub/discuss",
        data={"content": "Looks great, let us proceed!", "sender_name": "Alice"},
        follow_redirects=True,
    )
    assert client_discuss_resp.status_code == 200
    assert b"Looks great, let us proceed!" in client_discuss_resp.data

    # Client accepts the offer
    accept_resp = client.post(
        f"/request/{req_id}/hub/accept-offer/{offer_id}",
        follow_redirects=True,
    )
    assert accept_resp.status_code == 200
    assert b"ACCEPTED SQUAD" in accept_resp.data

    with app.app_context():
        updated_req = db.session.get(ProjectRequest, req_id)
        cu = db.session.get(CoderUser, coder_user.id)
        assert updated_req.status == "assigned"
        assert updated_req.assigned_group_id == cu.member.group_id
        accepted_offer = db.session.get(ProjectOffer, offer_id)
        assert accepted_offer.status == "accepted"
