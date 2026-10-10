from app.extensions import db
from app.models.group import Group
from app.models.project import Project
from app.models.member import Member
from app.models.coder_user import CoderUser
from app.models.audit_log import AuditLog


def test_coder_dashboard_and_profile(app, logged_in_coder_client, coder_user):
    # Dashboard
    resp = logged_in_coder_client.get("/coder/dashboard")
    assert resp.status_code == 200
    assert b"Welcome, coderdev!" in resp.data
    assert b"Alpha Crew" in resp.data

    # Profile GET
    prof_resp = logged_in_coder_client.get("/coder/profile")
    assert prof_resp.status_code == 200
    assert b"Coder Dev" in prof_resp.data

    # Profile POST update
    update_resp = logged_in_coder_client.post(
        "/coder/profile",
        data={
            "role": "Principal Software Engineer",
            "bio": "Expert in distributed backend systems.",
            "skill_tags": "python, flask, docker, kubernetes",
            "github_url": "https://github.com/coderdev",
        },
        follow_redirects=True,
    )
    assert update_resp.status_code == 200
    assert b"Your profile has been updated." in update_resp.data

    with app.app_context():
        member = db.session.get(Member, coder_user.member_id)
        assert member.role == "Principal Software Engineer"
        assert "kubernetes" in member.skill_tags

        # Audit row created
        audit = AuditLog.query.filter_by(action="member.coder_edited", actor_id=str(coder_user.id)).first()
        assert audit is not None


def test_coder_project_create_and_edit_scoped_to_group(app, logged_in_coder_client, coder_user):
    # Create project via /coder/projects/new
    create_resp = logged_in_coder_client.post(
        "/coder/projects/new",
        data={
            "title": "Alpha Cloud Service",
            "summary": "Cloud microservices deployment.",
            "description": "Full-stack project deployed on AWS.",
            "tech_tags": "aws, terraform, go",
            "live_url": "https://alphacloud.example",
        },
        follow_redirects=True,
    )
    assert create_resp.status_code == 200
    assert b"Alpha Cloud Service" in create_resp.data

    with app.app_context():
        proj = Project.query.filter_by(title="Alpha Cloud Service").first()
        assert proj is not None
        coder = db.session.get(CoderUser, coder_user.id)
        assert proj.group_id == coder.member.group_id
        assert proj.created_by_coder_id == coder_user.id
        assert proj.featured is False  # Coders cannot mark featured

        proj_id = proj.id

    # Edit project in own group
    edit_resp = logged_in_coder_client.post(
        f"/coder/projects/{proj_id}/edit",
        data={
            "title": "Alpha Cloud Service v2",
            "summary": "Updated cloud deployment.",
            "description": "Full-stack project with auto-scaling.",
            "tech_tags": "aws, terraform, go, k8s",
            "live_url": "https://alphacloud.example",
        },
        follow_redirects=True,
    )
    assert edit_resp.status_code == 200

    with app.app_context():
        updated_proj = db.session.get(Project, proj_id)
        assert updated_proj.title == "Alpha Cloud Service v2"
        assert updated_proj.last_edited_by_coder_id == coder_user.id


def test_coder_cannot_edit_other_group_project(app, logged_in_coder_client, coder_user):
    with app.app_context():
        # Create another group and project
        other_group = Group(name="Beta Crew", slug="beta-crew")
        db.session.add(other_group)
        db.session.flush()

        other_proj = Project(
            group_id=other_group.id,
            title="Beta Private Project",
            slug="beta-private-project",
            description="Confidential project for beta crew.",
        )
        db.session.add(other_proj)
        db.session.commit()
        other_proj_id = other_proj.id

    # Coder attempts to edit Beta crew's project -> returns 404
    resp = logged_in_coder_client.get(f"/coder/projects/{other_proj_id}/edit")
    assert resp.status_code == 404

    post_resp = logged_in_coder_client.post(
        f"/coder/projects/{other_proj_id}/edit",
        data={"title": "Hacked Title"},
    )
    assert post_resp.status_code == 404
