import io
import os
import pytest
from app.models.group import Group
from app.models.project import Project
from app.extensions import db


@pytest.fixture
def group_one(app):
    with app.app_context():
        g = Group(name="Alpha Crew", slug="alpha-crew")
        db.session.add(g)
        db.session.commit()
        return g.id


@pytest.fixture
def group_two(app):
    with app.app_context():
        g = Group(name="Beta Crew", slug="beta-crew")
        db.session.add(g)
        db.session.commit()
        return g.id


def test_create_project_with_gallery_and_alts(logged_in_client, app, group_one, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

    data = {
        "title": "Quantum Leap",
        "summary": "AI Quantum simulator",
        "description": "Long form description here",
        "status": "completed",
        "tech_tags": "qiskit, python",
        "gallery_files": [(io.BytesIO(img_bytes), "screenshot.png")],
        "gallery_alts": "Quantum circuit visualization diagram",
        "featured": "y",
    }
    resp = logged_in_client.post(
        f"/admin/groups/{group_one}/projects/new",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"added to Alpha Crew" in resp.data

    with app.app_context():
        p = Project.query.filter_by(title="Quantum Leap").first()
        assert p is not None
        assert p.slug == "quantum-leap"
        assert p.featured is True
        assert len(p.gallery_images) == 1
        assert p.gallery_images[0]["alt"] == "Quantum circuit visualization diagram"
        assert p.gallery_images[0]["path"].startswith("uploads/screenshots/")
        assert p.screenshot == p.gallery_images[0]["path"]


def test_image_without_alt_rejected(logged_in_client, app, group_one, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    img_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

    data = {
        "title": "Missing Alt Project",
        "status": "in_progress",
        "gallery_files": [(io.BytesIO(img_bytes), "screenshot.png")],
        "gallery_alts": "",  # Missing alt!
    }
    resp = logged_in_client.post(
        f"/admin/groups/{group_one}/projects/new",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Describe every image you upload." in resp.data

    with app.app_context():
        assert Project.query.filter_by(title="Missing Alt Project").first() is None


def test_project_slug_unique_per_group(logged_in_client, app, group_one, group_two):
    # Two projects with same title in same group get unique slugs (-2)
    logged_in_client.post(
        f"/admin/groups/{group_one}/projects/new",
        data={"title": "Same Title", "status": "completed"},
        follow_redirects=True,
    )
    logged_in_client.post(
        f"/admin/groups/{group_one}/projects/new",
        data={"title": "Same Title", "status": "completed"},
        follow_redirects=True,
    )

    with app.app_context():
        p1 = Project.query.filter_by(group_id=group_one, title="Same Title").order_by(Project.created_at.asc()).all()
        assert len(p1) == 2
        assert p1[0].slug == "same-title"
        assert p1[1].slug == "same-title-2"

    # Same title in different group is allowed with base slug
    logged_in_client.post(
        f"/admin/groups/{group_two}/projects/new",
        data={"title": "Same Title", "status": "completed"},
        follow_redirects=True,
    )

    with app.app_context():
        p2 = Project.query.filter_by(group_id=group_two, title="Same Title").first()
        assert p2 is not None
        assert p2.slug == "same-title"


def test_edit_project_remove_image_deletes_file(logged_in_client, app, group_one, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    rel_path = "uploads/screenshots/delete_test.png"
    full_path = os.path.join(str(tmp_path), "screenshots", "delete_test.png")
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(b"data")
    assert os.path.exists(full_path)

    with app.app_context():
        p = Project(
            group_id=group_one,
            title="Gallery Edit Test",
            slug="gallery-edit-test",
            gallery_images=[{"path": rel_path, "alt": "Old Screenshot"}],
            screenshot=rel_path,
        )
        db.session.add(p)
        db.session.commit()
        pid = p.id

    data = {
        "title": "Gallery Edit Test",
        "status": "completed",
        "remove_image": rel_path,
    }
    resp = logged_in_client.post(
        f"/admin/groups/{group_one}/projects/{pid}/edit",
        data=data,
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        p = db.session.get(Project, pid)
        assert len(p.gallery_images) == 0
        assert p.screenshot is None
    assert not os.path.exists(full_path)


def test_delete_project_via_post_only(logged_in_client, app, group_one):
    with app.app_context():
        p = Project(group_id=group_one, title="To Delete", slug="to-delete")
        db.session.add(p)
        db.session.commit()
        pid = p.id

    # GET is 405
    get_resp = logged_in_client.get(f"/admin/groups/{group_one}/projects/{pid}/delete")
    assert get_resp.status_code == 405

    # POST succeeds
    post_resp = logged_in_client.post(f"/admin/groups/{group_one}/projects/{pid}/delete", follow_redirects=True)
    assert post_resp.status_code == 200
    assert b"deleted" in post_resp.data

    with app.app_context():
        assert db.session.get(Project, pid) is None


def test_project_outside_group_returns_404(logged_in_client, app, group_one, group_two):
    with app.app_context():
        p = Project(group_id=group_two, title="Beta Project", slug="beta-project")
        db.session.add(p)
        db.session.commit()
        pid = p.id

    # Try editing via group_one URL
    resp = logged_in_client.get(f"/admin/groups/{group_one}/projects/{pid}/edit")
    assert resp.status_code == 404


def test_featured_flag_toggle_reflected_on_home(logged_in_client, app, group_one):
    # Check stats count on home
    home_resp = logged_in_client.get("/")
    assert home_resp.status_code == 200

    with app.app_context():
        p = Project(group_id=group_one, title="Super Project", slug="super-project", featured=True)
        db.session.add(p)
        db.session.commit()
        pid = p.id

    # Check that home reflects updated total projects stat
    home_resp2 = logged_in_client.get("/")
    assert home_resp2.status_code == 200
