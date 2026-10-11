import io
import pytest
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project
from app.extensions import db


def test_groups_list_requires_login(client):
    resp = client.get("/admin/groups")
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_groups_list_ok(logged_in_client, app):
    with app.app_context():
        g = Group(name="Test Group List", slug="test-group-list")
        db.session.add(g)
        db.session.commit()

    resp = logged_in_client.get("/admin/groups")
    assert resp.status_code == 200
    assert b"Test Group List" in resp.data
    assert b"Groups" in resp.data


def test_create_group_success(logged_in_client, app):
    data = {
        "name": "Innovators Hub",
        "tagline": "Building the future",
        "description": "Full description of innovators hub",
        "tech_tags": "Python, Flask, AI",
        "location": "San Francisco",
        "github_url": "https://github.com/example",
        "website_url": "https://example.com",
        "linkedin_url": "",
        "featured": "y",
    }
    resp = logged_in_client.post("/admin/groups/new", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"created successfully" in resp.data

    with app.app_context():
        g = Group.query.filter_by(name="Innovators Hub").first()
        assert g is not None
        assert g.slug == "innovators-hub"
        assert g.tech_tags == ["python", "flask", "ai"]
        assert g.featured is True

    # Verify public page is immediately accessible
    pub_resp = logged_in_client.get(f"/group/{g.slug}")
    assert pub_resp.status_code == 200
    assert b"Innovators Hub" in pub_resp.data


def test_create_group_validation_errors(logged_in_client, app):
    # Empty name should fail validation
    data = {
        "name": "",
        "tagline": "Just a tagline",
    }
    resp = logged_in_client.post("/admin/groups/new", data=data)
    assert resp.status_code == 200
    assert b"Group name is required." in resp.data or b"field is required" in resp.data.lower()

    with app.app_context():
        assert Group.query.count() == 0


def test_duplicate_names_get_unique_slugs(logged_in_client, app):
    logged_in_client.post("/admin/groups/new", data={"name": "Duplicate Team"}, follow_redirects=True)
    logged_in_client.post("/admin/groups/new", data={"name": "Duplicate Team"}, follow_redirects=True)

    with app.app_context():
        groups = Group.query.filter_by(name="Duplicate Team").all()
        assert len(groups) == 2
        slugs = {g.slug for g in groups}
        assert "duplicate-team" in slugs
        assert "duplicate-team-2" in slugs


def test_edit_group_keeps_slug_and_updates_fields(logged_in_client, app):
    with app.app_context():
        g = Group(name="Old Name", slug="old-name", tagline="Old tagline")
        db.session.add(g)
        db.session.commit()
        gid = g.id

    data = {
        "name": "Old Name",
        "tagline": "Updated tagline",
        "description": "Updated desc",
        "tech_tags": "React, TypeScript",
        "location": "London",
    }
    resp = logged_in_client.post(f"/admin/groups/{gid}/edit", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"updated successfully" in resp.data

    with app.app_context():
        g = db.session.get(Group, gid)
        assert g.slug == "old-name"  # unchanged
        assert g.tagline == "Updated tagline"
        assert g.tech_tags == ["react", "typescript"]


def test_delete_group_cascades_members_and_projects(logged_in_client, app):
    with app.app_context():
        g = Group(name="To Delete", slug="to-delete")
        db.session.add(g)
        db.session.commit()

        m = Member(group_id=g.id, name="Member 1")
        p = Project(group_id=g.id, title="Project 1", slug="project-1")
        db.session.add_all([m, p])
        db.session.commit()
        gid = g.id
        mid = m.id
        pid = p.id

    resp = logged_in_client.post(f"/admin/groups/{gid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert b"deleted" in resp.data

    with app.app_context():
        assert db.session.get(Group, gid) is None
        assert db.session.get(Member, mid) is None
        assert db.session.get(Project, pid) is None


def test_delete_requires_post(logged_in_client, app):
    with app.app_context():
        g = Group(name="No Get Delete", slug="no-get-delete")
        db.session.add(g)
        db.session.commit()
        gid = g.id

    resp = logged_in_client.get(f"/admin/groups/{gid}/delete")
    assert resp.status_code == 405


def test_logo_upload_valid_and_invalid(logged_in_client, app, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    # Valid PNG header (\x89PNG\r\n\x1a\n)
    valid_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    data = {
        "name": "PNG Group",
        "logo": (io.BytesIO(valid_png_bytes), "logo.png"),
    }
    resp = logged_in_client.post("/admin/groups/new", data=data, content_type="multipart/form-data", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        g = Group.query.filter_by(name="PNG Group").first()
        assert g.logo_path is not None
        assert g.logo_path.startswith("uploads/logos/")

    # Invalid fake PNG
    fake_png_data = {
        "name": "Fake PNG Group",
        "logo": (io.BytesIO(b"Fake header plain text"), "fake.png"),
    }
    resp2 = logged_in_client.post("/admin/groups/new", data=fake_png_data, content_type="multipart/form-data", follow_redirects=True)
    assert resp2.status_code == 200
    assert b"header" in resp2.data or b"error" in resp2.data.lower()
    with app.app_context():
        assert Group.query.filter_by(name="Fake PNG Group").first() is None


def test_public_site_reads_live_data(logged_in_client, app):
    with app.app_context():
        g = Group(name="Live Group", slug="live-group")
        db.session.add(g)
        db.session.commit()
        gid = g.id

    # Check directory
    resp = logged_in_client.get("/groups")
    assert b"Live Group" in resp.data

    # Edit via admin
    logged_in_client.post(
        f"/admin/groups/{gid}/edit",
        data={"name": "Live Group Renamed"},
        follow_redirects=True,
    )

    # Check directory again
    resp2 = logged_in_client.get("/groups")
    assert b"Live Group Renamed" in resp2.data


def test_create_and_edit_group_with_skill_proficiencies(logged_in_client, app):
    # 1. Create a group with tag:percentage format
    data = {
        "name": "Fullstack Ninjas",
        "tagline": "Mastering web technologies",
        "description": "Elite fullstack engineering guild.",
        "tech_tags": "Python:95, TypeScript:90, Docker:80",
    }
    resp = logged_in_client.post("/admin/groups/new", data=data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"created successfully" in resp.data

    with app.app_context():
        group = Group.query.filter_by(name="Fullstack Ninjas").first()
        assert group is not None
        assert group.tech_tags == ["python", "typescript", "docker"]
        assert group.skills_proficiencies == {"python": 95, "typescript": 90, "docker": 80}
        gid = group.id
        slug = group.slug

    # 2. Check public detail page displays exact percentage values and progress bars
    pub_resp = logged_in_client.get(f"/group/{slug}")
    assert pub_resp.status_code == 200
    assert b"95%" in pub_resp.data
    assert b"90%" in pub_resp.data
    assert b"80%" in pub_resp.data
    assert b'style="width: 95%;"' in pub_resp.data
    assert b'style="width: 90%;"' in pub_resp.data
    assert b'style="width: 80%;"' in pub_resp.data

    # 3. Check edit form pre-populates with tag:percentage format
    edit_get = logged_in_client.get(f"/admin/groups/{gid}/edit")
    assert edit_get.status_code == 200
    assert b"python:95, typescript:90, docker:80" in edit_get.data

    # 4. Update the skills in edit form
    update_data = {
        "name": "Fullstack Ninjas",
        "tech_tags": "Python:98, Go:88",
    }
    edit_post = logged_in_client.post(f"/admin/groups/{gid}/edit", data=update_data, follow_redirects=True)
    assert edit_post.status_code == 200
    assert b"updated successfully" in edit_post.data

    with app.app_context():
        updated_group = db.session.get(Group, gid)
        assert updated_group.tech_tags == ["python", "go"]
        assert updated_group.skills_proficiencies == {"python": 98, "go": 88}

    # Verify updated percentages render on public page
    pub_resp2 = logged_in_client.get(f"/group/{slug}")
    assert b"98%" in pub_resp2.data
    assert b"88%" in pub_resp2.data

