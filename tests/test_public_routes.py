import re
import pytest
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project
from app.services.sample_data import create_sample_data


@pytest.fixture
def sample_groups(app):
    with app.app_context():
        create_sample_data()


def test_home_200_and_stats(client, sample_groups):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    group_count = Group.query.count()
    member_count = Member.query.count()
    project_count = Project.query.count()

    assert f'data-number="{group_count}"' in html
    assert f'data-number="{member_count}"' in html
    assert f'data-number="{project_count}"' in html
    assert "Groups" in html
    assert "Members" in html
    assert "Projects" in html


def test_home_empty_state(client):
    # Empty DB
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "No groups yet." in html


def test_groups_directory_pagination(client, sample_groups):
    resp = client.get("/groups?page=1")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'id="directory-results"' in html

    # Out of range page returns 200 with no error
    resp_empty = client.get("/groups?page=99")
    assert resp_empty.status_code == 200


def test_group_detail_ok_and_404(client, sample_groups):
    # Known slug
    resp = client.get("/group/acme-devs")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Acme Devs" in html

    # Verify five anchor sections exist
    assert 'id="about"' in html
    assert 'id="team"' in html
    assert 'id="tech-stack"' in html
    assert 'id="projects"' in html
    assert 'id="contact"' in html

    # Unknown slug returns 404
    resp_404 = client.get("/group/nonexistent-group-slug")
    assert resp_404.status_code == 404


def test_group_detail_blank_member_project_lists(client, app):
    with app.app_context():
        empty_group = Group(
            name="Empty Squad",
            slug="empty-squad",
            description="A team without members or projects yet.",
            founded_year=2024,
        )
        db.session.add(empty_group)
        db.session.commit()

    resp = client.get("/group/empty-squad")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "No members yet." in html
    assert "No projects yet." in html


def test_resume_icon_only_when_resume_exists(client, sample_groups):
    # Acme Devs has Alex Vance with a resume
    resp_with_resume = client.get("/group/acme-devs")
    assert resp_with_resume.status_code == 200
    html_with = resp_with_resume.get_data(as_text=True)
    assert "Download Alex Vance's resume" in html_with

    # Binary Brains has members without resumes
    resp_no_resume = client.get("/group/binary-brains")
    assert resp_no_resume.status_code == 200
    html_without = resp_no_resume.get_data(as_text=True)
    assert "Download Marcus Stone's resume" not in html_without


def test_every_image_has_alt(client, sample_groups):
    resp = client.get("/group/acme-devs")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    img_tags = re.findall(r'<img[^>]+>', html)
    assert len(img_tags) > 0
    for img in img_tags:
        assert 'alt="' in img
        # Assert alt is not empty
        alt_match = re.search(r'alt="([^"]*)"', img)
        assert alt_match is not None
        assert len(alt_match.group(1).strip()) > 0, f"Found empty alt attribute in tag: {img}"


def test_no_bookmark_markup(client, sample_groups):
    resp = client.get("/group/acme-devs")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "bookmark" not in html.lower()
    assert "saved (" not in html.lower()
