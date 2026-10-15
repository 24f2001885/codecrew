import pytest
from datetime import datetime, timezone
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.coder_user import CoderUser
from app.models.project_request import ProjectRequest
from app.models.request_access_grant import RequestAccessGrant
from app.models.project_discussion import ProjectDiscussionMessage
from app.models.squad_review import SquadReview
from app.models.app_notification import AppNotification
from app.services.notifications import create_notification, get_unread_count


def test_submit_squad_review_flow(app, client):
    with app.app_context():
        group = Group(name="Review Team", slug="review-team")
        db.session.add(group)
        db.session.flush()

        member = Member(name="Dev Jane", group_id=group.id, role="Lead")
        db.session.add(member)
        db.session.flush()

        coder = CoderUser(
            member_id=member.id,
            username="devjane",
            email="devjane@example.com",
            status="active",
        )
        coder.set_password("DevJane1234!")
        db.session.add(coder)

        req = ProjectRequest(
            name="Alice Smith",
            email="alice@example.com",
            company="Smith Enterprises",
            project_type="fullstack",
            description="Build our e-commerce platform.",
            status="completed",
            assigned_group_id=group.id,
        )
        db.session.add(req)
        db.session.commit()

        req_id = req.id
        group_id = group.id
        coder_id = coder.id

    # Post review from request hub
    resp = client.post(
        f"/request/{req_id}/hub/review",
        data={
            "rating": "5",
            "review_title": "Outstanding work!",
            "comment": "The team delivered on time and our users love the UI.",
            "client_name": "Alice Smith",
            "client_company": "Smith Enterprises",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Thank you! Your verified client review" in resp.data

    with app.app_context():
        rev = SquadReview.query.filter_by(project_request_id=req_id).first()
        assert rev is not None
        assert rev.rating == 5
        assert rev.verified is True
        assert rev.review_title == "Outstanding work!"
        assert rev.group_id == group_id

        # Verify group computed properties
        g = db.session.get(Group, group_id)
        assert g.reviews_count == 1
        assert g.average_rating == 5.0

        # Verify notification was dispatched to coder
        notif = AppNotification.query.filter_by(
            recipient_type="coder",
            recipient_id=str(coder_id),
            category="review_received",
        ).first()
        assert notif is not None
        assert "New Verified Client Review" in notif.title
        assert "5/5 stars" in notif.message

    # Duplicate review should be rejected
    dup_resp = client.post(
        f"/request/{req_id}/hub/review",
        data={
            "rating": "4",
            "comment": "Another review attempt.",
        },
        follow_redirects=True,
    )
    assert dup_resp.status_code == 200
    assert b"You have already submitted a review" in dup_resp.data


def test_submit_squad_review_validation(app, client):
    with app.app_context():
        group = Group(name="Valid Team", slug="valid-team")
        db.session.add(group)
        db.session.flush()

        # In review status (not completed)
        req = ProjectRequest(
            name="Bob",
            email="bob@example.com",
            project_type="web",
            description="Ongoing project.",
            status="in_review",
            assigned_group_id=group.id,
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    # Trying to review incomplete project
    resp = client.post(
        f"/request/{req_id}/hub/review",
        data={"rating": "5", "comment": "Too early"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Reviews can only be submitted once the project is completed" in resp.data

    # Change status to completed but submit invalid rating
    with app.app_context():
        r = db.session.get(ProjectRequest, req_id)
        r.status = "completed"
        db.session.commit()

    bad_rating_resp = client.post(
        f"/request/{req_id}/hub/review",
        data={"rating": "10", "comment": "Invalid rating"},
        follow_redirects=True,
    )
    assert bad_rating_resp.status_code == 200
    assert b"Please provide a rating between 1 and 5" in bad_rating_resp.data


def test_notification_api_coder(app, logged_in_coder_client, coder_user):
    with app.app_context():
        # Create unread notification for coder
        n = create_notification(
            recipient_type="coder",
            recipient_id=coder_user.id,
            title="Sprint Milestone Accepted",
            message="Your milestone deliverable was approved.",
            category="milestone_update",
            link_url="/coder/opportunities/1",
        )
        notif_id = n.id

    # Fetch recent notifications
    resp = logged_in_coder_client.get("/notifications/api/recent")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["unread_count"] >= 1
    items = [x for x in data["notifications"] if x["id"] == notif_id]
    assert len(items) == 1
    assert items[0]["title"] == "Sprint Milestone Accepted"
    assert items[0]["category"] == "milestone_update"
    assert items[0]["is_read"] is False

    # Mark as read
    read_resp = logged_in_coder_client.post(f"/notifications/api/{notif_id}/read")
    assert read_resp.status_code == 200
    assert read_resp.get_json()["success"] is True

    with app.app_context():
        updated_n = db.session.get(AppNotification, notif_id)
        assert updated_n.is_read is True


def test_notification_api_read_all(app, logged_in_coder_client, coder_user):
    with app.app_context():
        create_notification(
            recipient_type="coder",
            recipient_id=coder_user.id,
            title="Alert 1",
            message="Notice 1",
            category="general",
        )
        create_notification(
            recipient_type="coder",
            recipient_id=coder_user.id,
            title="Alert 2",
            message="Notice 2",
            category="general",
        )

    read_all_resp = logged_in_coder_client.post("/notifications/api/read-all")
    assert read_all_resp.status_code == 200
    assert read_all_resp.get_json()["success"] is True

    # Verify unread count is 0
    resp = logged_in_coder_client.get("/notifications/api/recent")
    assert resp.status_code == 200
    assert resp.get_json()["unread_count"] == 0


def test_live_discussion_endpoints(app, client, logged_in_coder_client, coder_user):
    with app.app_context():
        coder = db.session.get(CoderUser, coder_user.id)
        group = db.session.get(Group, coder.member.group_id)
        req = ProjectRequest(
            name="Charlie",
            email="charlie@example.com",
            project_type="mobile",
            description="Build iOS and Android client.",
            status="in_review",
            assigned_group_id=group.id,
        )
        db.session.add(req)
        db.session.flush()

        grant = RequestAccessGrant(
            project_request_id=req.id,
            coder_id=coder_user.id,
            scope="brief_and_contact",
            granted_at=datetime.now(timezone.utc),
        )
        db.session.add(grant)

        msg1 = ProjectDiscussionMessage(
            project_request_id=req.id,
            sender_type="client",
            sender_name="Charlie",
            content="Can you integrate Stripe payments?",
        )
        msg2 = ProjectDiscussionMessage(
            project_request_id=req.id,
            sender_type="coder",
            sender_name="Coder Dev",
            sender_coder_id=coder_user.id,
            content="Yes, absolutely. We have done many Stripe integrations.",
        )
        db.session.add(msg1)
        db.session.add(msg2)
        db.session.commit()
        req_id = req.id

    # Test client hub discussion JSON polling endpoint
    hub_resp = client.get(f"/request/{req_id}/hub/discussion/messages")
    assert hub_resp.status_code == 200
    hub_data = hub_resp.get_json()
    assert hub_data["count"] == 2
    assert len(hub_data["messages"]) == 2
    assert hub_data["messages"][0]["content"] == "Can you integrate Stripe payments?"

    # Test coder opportunity discussion JSON polling endpoint
    coder_resp = logged_in_coder_client.get(f"/coder/opportunities/{req_id}/discussion/messages")
    assert coder_resp.status_code == 200
    coder_data = coder_resp.get_json()
    assert coder_data["count"] == 2
    assert len(coder_data["messages"]) == 2
    assert coder_data["messages"][1]["content"] == "Yes, absolutely. We have done many Stripe integrations."
