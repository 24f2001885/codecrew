import io
import os
import pytest
from app.models.group import Group
from app.models.member import Member
from app.extensions import db


@pytest.fixture
def test_group(app):
    with app.app_context():
        g = Group(name="Engineering Team", slug="engineering-team")
        db.session.add(g)
        db.session.commit()
        return g.id


def test_member_list_scoped_to_group(logged_in_client, app, test_group):
    with app.app_context():
        g2 = Group(name="Design Team", slug="design-team")
        db.session.add(g2)
        db.session.commit()

        m1 = Member(group_id=test_group, name="Alice Eng")
        m2 = Member(group_id=g2.id, name="Bob Design")
        db.session.add_all([m1, m2])
        db.session.commit()

    resp = logged_in_client.get(f"/admin/groups/{test_group}/members")
    assert resp.status_code == 200
    assert b"Alice Eng" in resp.data
    assert b"Bob Design" not in resp.data


def test_create_member_with_photo_and_resume(logged_in_client, app, test_group, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    photo_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    pdf_bytes = b"%PDF-1.4 sample resume content"

    data = {
        "name": "Jane Doe",
        "role": "Lead Architect",
        "bio": "Experienced builder",
        "skill_tags": "Python, Docker, K8s",
        "display_order": "1",
        "photo": (io.BytesIO(photo_bytes), "jane.png"),
        "resume_pdf": (io.BytesIO(pdf_bytes), "jane_resume.pdf"),
    }
    resp = logged_in_client.post(
        f"/admin/groups/{test_group}/members/new",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Jane Doe" in resp.data

    with app.app_context():
        m = Member.query.filter_by(name="Jane Doe").first()
        assert m is not None
        assert m.photo_path.startswith("uploads/photos/")
        assert m.resume_pdf.startswith("uploads/resumes/")
        assert m.skill_tags == ["python", "docker", "k8s"]

    # Public group page shows resume button with aria-label
    pub_resp = logged_in_client.get("/group/engineering-team")
    assert pub_resp.status_code == 200
    assert b"Jane Doe" in pub_resp.data
    assert b"Jane Doe's resume" in pub_resp.data or b"Resume" in pub_resp.data


def test_resume_rejects_non_pdf(logged_in_client, app, test_group, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    # Uploading a docx or text file
    data = {
        "name": "Invalid File User",
        "resume_pdf": (io.BytesIO(b"Not a PDF file"), "resume.docx"),
    }
    resp = logged_in_client.post(
        f"/admin/groups/{test_group}/members/new",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"error" in resp.data.lower() or b"pdf" in resp.data.lower()


def test_resume_rejects_over_5mb(logged_in_client, app, test_group, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    # File larger than 5 MB
    large_pdf = b"%PDF-" + b"0" * (5 * 1024 * 1024 + 10)
    data = {
        "name": "Big PDF User",
        "resume_pdf": (io.BytesIO(large_pdf), "large.pdf"),
    }
    resp = logged_in_client.post(
        f"/admin/groups/{test_group}/members/new",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 413 or b"5 mb" in resp.data.lower() or b"error" in resp.data.lower()


def test_remove_resume_clears_field_and_deletes_file(logged_in_client, app, test_group, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    pdf_bytes = b"%PDF-1.4 sample content"
    with app.app_context():
        m = Member(
            group_id=test_group,
            name="Bob Resume",
            resume_pdf="uploads/resumes/dummy_test.pdf",
        )
        db.session.add(m)
        db.session.commit()
        mid = m.id

    # Create dummy file on disk
    full_path = os.path.join(str(tmp_path), "resumes", "dummy_test.pdf")
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(pdf_bytes)
    assert os.path.exists(full_path)

    # Post edit with remove_resume=y
    data = {
        "name": "Bob Resume",
        "remove_resume": "y",
    }
    resp = logged_in_client.post(
        f"/admin/groups/{test_group}/members/{mid}/edit",
        data=data,
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        m = db.session.get(Member, mid)
        assert m.resume_pdf is None
    assert not os.path.exists(full_path)


def test_edit_member_wrong_group_returns_404(logged_in_client, app, test_group):
    with app.app_context():
        g2 = Group(name="Other Group", slug="other-group")
        db.session.add(g2)
        db.session.commit()
        m = Member(group_id=g2.id, name="Other Member")
        db.session.add(m)
        db.session.commit()
        mid = m.id

    # Attempting to edit m through test_group should return 404
    resp = logged_in_client.get(f"/admin/groups/{test_group}/members/{mid}/edit")
    assert resp.status_code == 404


def test_delete_member_removes_files_and_row(logged_in_client, app, test_group, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    with app.app_context():
        m = Member(
            group_id=test_group,
            name="To Delete Member",
            photo_path="uploads/photos/delete_me.png",
        )
        db.session.add(m)
        db.session.commit()
        mid = m.id

    file_path = os.path.join(str(tmp_path), "photos", "delete_me.png")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(b"data")

    resp = logged_in_client.post(
        f"/admin/groups/{test_group}/members/{mid}/delete",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Member" in resp.data

    with app.app_context():
        assert db.session.get(Member, mid) is None
    assert not os.path.exists(file_path)


def test_skill_tags_normalized_lowercase_unique(logged_in_client, app, test_group):
    data = {
        "name": "Tagged Member",
        "skill_tags": "Python, FLASK, python, Docker,   REACT  ",
    }
    resp = logged_in_client.post(
        f"/admin/groups/{test_group}/members/new",
        data=data,
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        m = Member.query.filter_by(name="Tagged Member").first()
        assert m.skill_tags == ["python", "flask", "docker", "react"]
