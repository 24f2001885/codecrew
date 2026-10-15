from datetime import datetime, timedelta
import pytest
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project
from app.models.blog_post import BlogPost


def test_group_landing_page_full_showcase(client, app):
    with app.app_context():
        g = Group(
            name="Quantum Collective",
            slug="quantum-collective",
            tagline="Next-generation distributed computing squad",
            description="Quantum Collective develops fault-tolerant distributed systems and algorithms.",
            location="San Francisco, CA",
            founded_year=2023,
            tech_tags=["rust", "grpc", "kubernetes"],
            skills_proficiencies={"rust": 95, "grpc": 90, "kubernetes": 85},
            social_links={
                "github": "https://github.com/quantum-collective",
                "website": "https://quantum.example",
                "linkedin": "https://linkedin.com/company/quantum-collective",
            },
            featured=True,
        )
        db.session.add(g)
        db.session.flush()

        m1 = Member(
            name="Dr. Elena Vance",
            role="Distributed Systems Architect",
            group_id=g.id,
            skill_tags=["rust", "grpc"],
            bio="Lead architect designing consensus protocols.",
            github_url="https://github.com/elena",
        )
        p1 = Project(
            title="MeshSync Engine",
            slug="meshsync-engine",
            summary="Zero-copy synchronization for edge clusters",
            description="Real-time multi-region replication engine with verifiable state transitions.",
            group_id=g.id,
            tech_tags=["rust", "grpc"],
            status="completed",
            demo_url="https://meshsync.example",
            github_url="https://github.com/quantum-collective/meshsync",
        )
        b1 = BlogPost(
            title="Consensus at the Edge",
            slug="consensus-at-the-edge",
            content="Deep dive into optimizing consensus roundtrips across high latency WAN connections.",
            group_id=g.id,
            tags=["Distributed Systems", "Rust"],
            published_at=datetime.utcnow() - timedelta(days=2),
        )
        db.session.add_all([m1, p1, b1])
        db.session.commit()

    # Request the group landing page
    res = client.get("/group/quantum-collective")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # 1. Hero & Badges
    assert "Quantum Collective" in html
    assert "Next-generation distributed computing squad" in html
    assert "Featured Collective" in html
    assert "San Francisco, CA" in html
    assert "Est. 2023" in html
    assert "Share Squad" in html
    assert "https://github.com/quantum-collective" in html
    assert "https://quantum.example" in html

    # 2. Section Anchors
    assert 'id="about"' in html
    assert 'id="team"' in html
    assert 'id="tech-stack"' in html
    assert 'id="projects"' in html
    assert 'id="blog"' in html
    assert 'id="contact"' in html

    # 3. Team Member
    assert "Dr. Elena Vance" in html
    assert "Distributed Systems Architect" in html

    # 4. Project Showcase
    assert "MeshSync Engine" in html
    assert "https://meshsync.example" in html
    assert "project-modal-" in html

    # 5. Dev Log / Blog
    assert "Consensus at the Edge" in html

    # 6. Contact Form
    assert 'action="/group/quantum-collective/contact"' in html


def test_group_landing_page_graceful_empty_states(client, app):
    with app.app_context():
        g = Group(
            name="Nascent Labs",
            slug="nascent-labs",
            description="A brand new team just getting started.",
        )
        db.session.add(g)
        db.session.commit()

    res = client.get("/group/nascent-labs")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    assert "Nascent Labs" in html
    assert "No members yet." in html
    assert "No projects yet." in html
    assert "No dev log entries published yet." in html
    assert 'id="contact"' in html
