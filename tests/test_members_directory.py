import re
import pytest
from app.extensions import db
from app.models.group import Group
from app.models.member import Member


@pytest.fixture
def members_seed(app):
    with app.app_context():
        g1 = Group(name="Alpha Collective", slug="alpha-collective")
        g2 = Group(name="Beta Collective", slug="beta-collective")
        db.session.add_all([g1, g2])
        db.session.commit()

        # Member with resume and skills
        m1 = Member(
            group_id=g1.id,
            name="Diana Prince",
            role="Lead Architect",
            skill_tags=["python", "fastapi"],
            resume_pdf_path="resumes/alpha_collective/diana.pdf",
            photo_path="photos/diana.jpg",
        )
        # Member without resume and without skills
        m2 = Member(
            group_id=g2.id,
            name="Clark Kent",
            role="Systems Engineer",
            skill_tags=[],
            resume_pdf_path=None,
            photo_path=None,
        )
        db.session.add_all([m1, m2])
        db.session.commit()
        return g1.id, g2.id


def test_members_page_lists_members_from_all_groups(client, members_seed):
    resp = client.get("/members")
    assert resp.status_code == 200
    assert b"Diana Prince" in resp.data
    assert b"Clark Kent" in resp.data
    assert b"Alpha Collective" in resp.data
    assert b"Beta Collective" in resp.data


def test_resume_button_only_when_resume_exists_and_has_aria_label(client, members_seed):
    resp = client.get("/members")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Diana has resume with required aria-label
    assert 'aria-label="Download Diana Prince\'s resume"' in html

    # Clark Kent has no resume
    assert 'aria-label="Download Clark Kent\'s resume"' not in html


def test_group_badge_links_to_group_page(client, members_seed):
    resp = client.get("/members")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert '/group/alpha-collective' in html
    assert '/group/beta-collective' in html


def test_member_without_skill_tags_renders_without_empty_tag_list(client, members_seed):
    resp = client.get("/members")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Extract card for Clark Kent
    start_pos = html.find("Clark Kent")
    assert start_pos != -1
    card_section = html[start_pos : start_pos + 600]
    # Should not contain <div class="skill-tags">
    assert '<div class="skill-tags' not in card_section


def test_members_page_images_have_alt(client, members_seed):
    resp = client.get("/members")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # Find all <img> tags and ensure every single one has an alt attribute
    img_tags = re.findall(r"<img[^>]*>", html)
    assert len(img_tags) > 0
    for img in img_tags:
        assert 'alt="' in img, f"Img tag missing alt attribute: {img}"


def test_members_page_works_without_js(client, members_seed):
    # Server-rendered initial HTML response contains full card data without needing client JS
    resp = client.get("/members")
    assert resp.status_code == 200
    assert b"id=\"directory-results\"" in resp.data
    assert b"Diana Prince" in resp.data
    assert b"Lead Architect" in resp.data
