import io
import os
from pathlib import Path
import pytest
from app.models.group import Group
from app.models.project_request import ProjectRequest
from app.extensions import db, mail


@pytest.fixture
def test_group(app):
    with app.app_context():
        g = Group(name="Backend Team", slug="backend-team")
        db.session.add(g)
        db.session.commit()
        return g.id


def test_request_form_get_200(client):
    resp = client.get("/request-project")
    assert resp.status_code == 200
    assert b"Tell Us What You Want Built" in resp.data
    assert b"Project Description" in resp.data


def test_request_valid_creates_row_status_new_and_mail(client, app):
    data = {
        "name": "David Client",
        "email": "david@client.com",
        "company": "Tech Corp",
        "project_type": "web_app",
        "budget_range": "$10,000 - $20,000",
        "timeline": "3 months",
        "description": "We need a comprehensive inventory management web application with real-time sync.",
    }

    with mail.record_messages() as outbox:
        resp = client.post("/request-project", data=data, follow_redirects=True)
        assert resp.status_code == 200
        assert b"received your request" in resp.data

        with app.app_context():
            req = ProjectRequest.query.filter_by(email="david@client.com").first()
            assert req is not None
            assert req.name == "David Client"
            assert req.status == "new"
            assert req.attachment_path is None

        assert len(outbox) == 1
        assert "New Project Request" in outbox[0].subject


def test_request_with_pdf_saved_privately(client, app, tmp_path):
    app.config["PRIVATE_UPLOAD_FOLDER"] = str(tmp_path / "private_uploads")
    pdf_bytes = b"%PDF-1.4 confidential project brief contents"

    data = {
        "name": "Private Client",
        "email": "private@client.com",
        "project_type": "api_backend",
        "description": "Building high scale distributed backend API services for fintech platform.",
        "attachment": (io.BytesIO(pdf_bytes), "brief.pdf"),
    }

    resp = client.post("/request-project", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        req = ProjectRequest.query.filter_by(email="private@client.com").first()
        assert req is not None
        assert req.attachment_path is not None
        assert req.attachment_path.endswith(".pdf")
        # Ensure it is NOT the original filename
        assert req.attachment_path != "brief.pdf"

        # Check file exists in private folder
        private_file = Path(app.config["PRIVATE_UPLOAD_FOLDER"]) / "requests" / req.attachment_path
        assert private_file.exists()

    # Verify that trying to access it via static uploads is 404
    static_resp = client.get(f"/static/uploads/{req.attachment_path}")
    assert static_resp.status_code == 404


def test_request_rejects_bad_attachment_type_and_size(client, app, tmp_path):
    app.config["PRIVATE_UPLOAD_FOLDER"] = str(tmp_path / "private_uploads")
    # File with invalid header (fake pdf)
    data = {
        "name": "Bad File User",
        "email": "bad@client.com",
        "project_type": "mobile_app",
        "description": "Attempting to upload executable or text file disguised as PDF format.",
        "attachment": (io.BytesIO(b"Fake executable header not PDF"), "evil.pdf"),
    }
    resp = client.post("/request-project", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert b"signature" in resp.data.lower() or b"error" in resp.data.lower()

    with app.app_context():
        assert ProjectRequest.query.filter_by(email="bad@client.com").first() is None


def test_request_honeypot_silent(client, app):
    data = {
        "name": "Spam Requester",
        "email": "spam@bot.com",
        "project_type": "other",
        "description": "Spam payload advertisement text across multiple lines for testing.",
        "website": "http://spambot.xyz",  # Honeypot!
    }
    resp = client.post("/request-project", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"received your request" in resp.data

    with app.app_context():
        assert ProjectRequest.query.filter_by(name="Spam Requester").first() is None


def test_admin_inbox_lists_request_and_status_change_persists(logged_in_client, app):
    with app.app_context():
        r = ProjectRequest(
            name="Inbox Client",
            email="inbox@client.com",
            project_type="web_app",
            description="Testing admin status changes and list display.",
            status="new",
        )
        db.session.add(r)
        db.session.commit()
        rid = r.id

    # View inbox
    resp = logged_in_client.get("/admin/project-requests")
    assert resp.status_code == 200
    assert b"Inbox Client" in resp.data
    assert b"Project Requests" in resp.data

    # Change status to in_review
    resp_status = logged_in_client.post(
        f"/admin/project-requests/{rid}/status",
        data={"status": "in_review"},
        follow_redirects=True,
    )
    assert resp_status.status_code == 200

    with app.app_context():
        req = db.session.get(ProjectRequest, rid)
        assert req.status == "in_review"


def test_assign_group_sends_no_email(logged_in_client, app, test_group):
    with app.app_context():
        r = ProjectRequest(
            name="Assignment Client",
            email="assign@client.com",
            project_type="web_app",
            description="Testing team assignment behavior for project request.",
        )
        db.session.add(r)
        db.session.commit()
        rid = r.id

    with mail.record_messages() as outbox:
        # Assign group
        resp = logged_in_client.post(
            f"/admin/project-requests/{rid}/assign",
            data={"assigned_group_id": test_group},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        # No email should be sent upon assignment
        assert len(outbox) == 0

        with app.app_context():
            req = db.session.get(ProjectRequest, rid)
            assert req.assigned_group_id == test_group

        # Clear assignment
        resp_clear = logged_in_client.post(
            f"/admin/project-requests/{rid}/assign",
            data={"assigned_group_id": ""},
            follow_redirects=True,
        )
        assert resp_clear.status_code == 200
        assert len(outbox) == 0

        with app.app_context():
            req = db.session.get(ProjectRequest, rid)
            assert req.assigned_group_id is None


def test_delete_request_removes_private_file(logged_in_client, app, tmp_path):
    app.config["PRIVATE_UPLOAD_FOLDER"] = str(tmp_path / "private_uploads")
    stored_name = "test_del.pdf"
    private_file = Path(app.config["PRIVATE_UPLOAD_FOLDER"]) / "requests" / stored_name
    private_file.parent.mkdir(parents=True, exist_ok=True)
    with open(private_file, "wb") as f:
        f.write(b"%PDF-1.4 dummy")
    assert private_file.exists()

    with app.app_context():
        r = ProjectRequest(
            name="Delete Client",
            email="del@client.com",
            project_type="other",
            description="To be deleted request.",
            attachment_path=stored_name,
        )
        db.session.add(r)
        db.session.commit()
        rid = r.id

    resp = logged_in_client.post(f"/admin/project-requests/{rid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert db.session.get(ProjectRequest, rid) is None
    assert not private_file.exists()


def test_attachment_download_requires_login(client, app, tmp_path):
    app.config["PRIVATE_UPLOAD_FOLDER"] = str(tmp_path / "private_uploads")
    stored_name = "secret.pdf"
    private_file = Path(app.config["PRIVATE_UPLOAD_FOLDER"]) / "requests" / stored_name
    private_file.parent.mkdir(parents=True, exist_ok=True)
    with open(private_file, "wb") as f:
        f.write(b"%PDF-1.4 sample content")

    with app.app_context():
        r = ProjectRequest(
            name="Secret Client",
            email="secret@client.com",
            project_type="web_app",
            description="Confidential project specs attached.",
            attachment_path=stored_name,
        )
        db.session.add(r)
        db.session.commit()
        rid = r.id

    anon_resp = client.get(f"/admin/project-requests/{rid}/attachment")
    assert anon_resp.status_code == 302
    assert "/admin/login" in anon_resp.headers["Location"]


def test_attachment_download_admin_ok(logged_in_client, app, tmp_path):
    app.config["PRIVATE_UPLOAD_FOLDER"] = str(tmp_path / "private_uploads")
    stored_name = "secret.pdf"
    private_file = Path(app.config["PRIVATE_UPLOAD_FOLDER"]) / "requests" / stored_name
    private_file.parent.mkdir(parents=True, exist_ok=True)
    with open(private_file, "wb") as f:
        f.write(b"%PDF-1.4 sample content")

    with app.app_context():
        r = ProjectRequest(
            name="Secret Client",
            email="secret@client.com",
            project_type="web_app",
            description="Confidential project specs attached.",
            attachment_path=stored_name,
        )
        db.session.add(r)
        db.session.commit()
        rid = r.id

    # Logged-in admin downloads attachment
    auth_resp = logged_in_client.get(f"/admin/project-requests/{rid}/attachment")
    assert auth_resp.status_code == 200
    assert auth_resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert "attachment" in auth_resp.headers.get("Content-Disposition", "")
    assert auth_resp.data == b"%PDF-1.4 sample content"


def test_end_to_end_request_to_admin_status(client, logged_in_client, app):
    # 1. Public client submits request
    submit_data = {
        "name": "E2E Requester",
        "email": "e2e@company.com",
        "company": "E2E Enterprises",
        "project_type": "desktop_software",
        "description": "Full end to end test verification for project request lifecycle.",
    }
    submit_resp = client.post("/request-project", data=submit_data, follow_redirects=True)
    assert submit_resp.status_code == 200

    with app.app_context():
        req = ProjectRequest.query.filter_by(email="e2e@company.com").first()
        assert req is not None
        rid = req.id
        assert req.status == "new"

    # 2. Admin logs in and checks inbox
    inbox_resp = logged_in_client.get("/admin/project-requests")
    assert inbox_resp.status_code == 200
    assert b"E2E Requester" in inbox_resp.data

    # 3. Admin updates status to 'contacted'
    status_resp = logged_in_client.post(
        f"/admin/project-requests/{rid}/status",
        data={"status": "contacted"},
        follow_redirects=True,
    )
    assert status_resp.status_code == 200

    # 4. Verify persisted status
    with app.app_context():
        updated_req = db.session.get(ProjectRequest, rid)
        assert updated_req.status == "contacted"
