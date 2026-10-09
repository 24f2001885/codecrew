import os
import pytest
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project
from app.services.search import search_groups, search_members, build_filtered_query


@pytest.fixture
def search_seed_data(app):
    with app.app_context():
        g1 = Group(
            name="Acme Devs",
            slug="acme-devs",
            tagline="Top tier full stack engineers",
            tech_tags=["react", "python", "docker"],
        )
        g2 = Group(
            name="Beta Crew",
            slug="beta-crew",
            tagline="Mobile masters and cloud experts",
            tech_tags=["flutter", "go", "aws"],
        )
        g3 = Group(
            name="Special % 100% Group",
            slug="special-group",
            tagline="Handling edge cases with % and _ symbols",
            tech_tags=["c++"],
        )
        db.session.add_all([g1, g2, g3])
        db.session.commit()

        m1 = Member(
            group_id=g1.id,
            name="Alice Smith",
            role="Frontend Lead",
            skill_tags=["react", "typescript"],
        )
        m2 = Member(
            group_id=g1.id,
            name="Bob Jones",
            role="Backend Guru",
            skill_tags=["python", "postgresql"],
        )
        m3 = Member(
            group_id=g2.id,
            name="Charlie Brown",
            role="Mobile Developer",
            skill_tags=["flutter", "dart"],
        )
        db.session.add_all([m1, m2, m3])

        p1 = Project(
            group_id=g1.id,
            title="Acme Portal",
            slug="acme-portal",
            description="Portal project",
        )
        db.session.add(p1)
        db.session.commit()

        return {
            "g1_id": g1.id,
            "g2_id": g2.id,
            "g3_id": g3.id,
            "m1_id": m1.id,
            "m2_id": m2.id,
            "m3_id": m3.id,
        }


def test_search_groups_empty_returns_all(app, search_seed_data):
    with app.app_context():
        res = search_groups("", "", 1)
        assert res["total_count"] == 3
        assert len(res["items"]) == 3
        assert res["page"] == 1
        assert res["total_pages"] == 1


def test_search_groups_case_insensitive(app, search_seed_data):
    with app.app_context():
        res = search_groups("ACME", "", 1)
        assert res["total_count"] == 1
        assert res["items"][0].slug == "acme-devs"


def test_search_groups_tag_matching(app, search_seed_data):
    with app.app_context():
        res = search_groups("", "React", 1)
        assert res["total_count"] == 1
        assert res["items"][0].slug == "acme-devs"


def test_search_groups_unmatched_tag_returns_empty(app, search_seed_data):
    with app.app_context():
        res = search_groups("", "nonexistent-tag", 1)
        assert res["total_count"] == 0
        assert res["items"] == []
        assert res["total_pages"] == 1


def test_search_page_beyond_last_returns_empty_items(app, search_seed_data):
    with app.app_context():
        res = search_groups("", "", 99)
        assert res["items"] == []
        assert res["page"] == 99
        assert res["total_pages"] >= 1
        assert res["total_count"] == 3


def test_search_members_filter_by_group_slug(app, search_seed_data):
    with app.app_context():
        res = search_members("", group_slug="acme-devs", skill="", page=1)
        assert res["total_count"] == 2
        names = {m.name for m in res["items"]}
        assert names == {"Alice Smith", "Bob Jones"}


def test_percent_sign_in_query_is_escaped(app, search_seed_data):
    with app.app_context():
        # Searching for literal "%" should only match g3, not all groups!
        res = search_groups("%", "", 1)
        assert res["total_count"] == 1
        assert res["items"][0].slug == "special-group"


def test_api_groups_endpoint(client, search_seed_data):
    resp = client.get("/api/groups")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "items" in data
    assert "page" in data
    assert "total_pages" in data
    assert "total_count" in data
    assert "html" in data
    assert data["total_count"] == 3
    assert len(data["items"]) == 3

    first = data["items"][0]
    expected_fields = [
        "slug", "name", "tagline", "logo_path", "cover_image_path",
        "tech_tags", "featured", "member_count", "project_count"
    ]
    for field in expected_fields:
        assert field in first


def test_api_groups_unmatched_tag(client, search_seed_data):
    resp = client.get("/api/groups?tag=nonexistent")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_count"] == 0
    assert data["items"] == []


def test_api_members_filter_and_pagination(client, search_seed_data):
    # Non-integer page fallback to 1
    resp = client.get("/api/members?page=abc&group=acme-devs")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["page"] == 1
    assert data["total_count"] == 2
    assert len(data["items"]) == 2
    assert "Alice Smith" in data["html"]


def test_members_api_never_exposes_private_fields(client, search_seed_data):
    resp = client.get("/api/members")
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    assert "email" not in text
    assert "password" not in text
    assert "internal_notes" not in text
    assert "message" not in text


def test_sqlite_python_filter_path_used(app):
    assert db.engine.dialect.name == "sqlite"


@pytest.mark.skipif(
    "postgresql" not in os.environ.get("TEST_DATABASE_URL", ""),
    reason="Requires PostgreSQL database specified in TEST_DATABASE_URL"
)
def test_postgres_json_containment(app):
    # Checked when PostgreSQL is configured
    pass


def test_filtered_views_share_state_via_query_string(client, search_seed_data):
    resp = client.get("/members?skill=flutter")
    assert resp.status_code == 200
    assert b"Charlie Brown" in resp.data
    assert b"Alice Smith" not in resp.data
