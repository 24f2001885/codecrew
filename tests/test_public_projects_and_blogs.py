from datetime import datetime, timedelta
import pytest
from app.extensions import db
from app.models.group import Group
from app.models.project import Project
from app.models.blog_post import BlogPost


def test_public_projects_directory_and_home_showcase(client, app):
    with app.app_context():
        group = Group(name="Rocket Devs", slug="rocket-devs")
        db.session.add(group)
        db.session.flush()

        proj1 = Project(
            title="Cosmos Explorer",
            slug="cosmos-explorer",
            summary="Autonomous interstellar simulator",
            description="Deep space tracking and rendering with high performance.",
            group_id=group.id,
            tech_tags=["python", "opengl"],
            featured=True,
            demo_url="https://cosmos.example",
            github_url="https://github.com/example/cosmos",
        )
        proj2 = Project(
            title="Orbital Router",
            slug="orbital-router",
            summary="Low-latency routing protocol",
            description="High throughput packet switching for telemetry.",
            group_id=group.id,
            tech_tags=["rust", "network"],
            featured=False,
        )
        db.session.add_all([proj1, proj2])
        db.session.commit()

    # 1. Homepage showcases top projects
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert b"Top Projects Built by Collectives" in res_home.data
    assert b"Cosmos Explorer" in res_home.data
    assert b"/projects" in res_home.data

    # 2. Public /projects directory displays projects
    res_dir = client.get("/projects")
    assert res_dir.status_code == 200
    assert b"Top Projects" in res_dir.data
    assert b"Cosmos Explorer" in res_dir.data
    assert b"Orbital Router" in res_dir.data
    assert b"project-modal-" in res_dir.data
    assert b"Rocket Devs" in res_dir.data

    # 3. Filtering by tag
    res_tag = client.get("/projects?tag=python")
    assert res_tag.status_code == 200
    assert b"Cosmos Explorer" in res_tag.data
    assert b"Orbital Router" not in res_tag.data

    # 4. Filtering by group
    res_group = client.get("/projects?group=rocket-devs")
    assert res_group.status_code == 200
    assert b"Cosmos Explorer" in res_group.data


def test_public_blog_directory_and_reader(client, app):
    with app.app_context():
        group = Group(name="Cyber Squad", slug="cyber-squad")
        db.session.add(group)
        db.session.flush()

        published_post = BlogPost(
            title="Building High Concurrency Microservices",
            slug="building-high-concurrency-microservices",
            content="Full engineering post mortem on building async message queues and optimizing throughput.",
            group_id=group.id,
            tags=["Architecture", "Python"],
            published_at=datetime.utcnow() - timedelta(hours=2),
        )
        draft_post = BlogPost(
            title="Internal Work In Progress Draft",
            slug="internal-work-in-progress-draft",
            content="Unpublished secret internal design notes.",
            group_id=group.id,
            tags=["Secret"],
            published_at=None,
        )
        future_post = BlogPost(
            title="Scheduled Future Post",
            slug="scheduled-future-post",
            content="Should not be public yet.",
            group_id=group.id,
            tags=["Future"],
            published_at=datetime.utcnow() + timedelta(days=5),
        )
        db.session.add_all([published_post, draft_post, future_post])
        db.session.commit()

    # 1. Homepage showcases Dev Log
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert b"Dev Log &amp; Technical Articles" in res_home.data or b"Dev Log & Technical Articles" in res_home.data
    assert b"Building High Concurrency Microservices" in res_home.data
    assert b"Internal Work In Progress Draft" not in res_home.data

    # 2. Public /blog directory lists published posts only
    res_blog = client.get("/blog")
    assert res_blog.status_code == 200
    assert b"Dev Log &amp; Blog" in res_blog.data or b"Dev Log & Blog" in res_blog.data
    assert b"Building High Concurrency Microservices" in res_blog.data
    assert b"Internal Work In Progress Draft" not in res_blog.data
    assert b"Scheduled Future Post" not in res_blog.data

    # 3. Blog reader route /blog/<slug>
    res_reader = client.get("/blog/building-high-concurrency-microservices")
    assert res_reader.status_code == 200
    assert b"Full engineering post mortem on building async message queues" in res_reader.data
    assert b"Cyber Squad" in res_reader.data
    assert b"Copy Link" in res_reader.data

    # 4. Canonical group route /group/<group_slug>/blog/<slug>
    res_canon = client.get("/group/cyber-squad/blog/building-high-concurrency-microservices")
    assert res_canon.status_code == 200
    assert b"Building High Concurrency Microservices" in res_canon.data

    # 5. Drafts return 404 to public visitors
    res_draft = client.get("/blog/internal-work-in-progress-draft")
    assert res_draft.status_code == 404

    # 6. Future posts return 404 to public visitors
    res_future = client.get("/blog/scheduled-future-post")
    assert res_future.status_code == 404


def test_navbar_and_sitemap_links(client, app):
    with app.app_context():
        group = Group(name="Nav Crew", slug="nav-crew")
        db.session.add(group)
        db.session.flush()

        post = BlogPost(
            title="Sitemap Featured Post",
            slug="sitemap-featured-post",
            content="Indexed article content.",
            group_id=group.id,
            published_at=datetime.utcnow() - timedelta(days=1),
        )
        db.session.add(post)
        db.session.commit()

    # Navbar check
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert b'href="/projects"' in res_home.data
    assert b'href="/blog"' in res_home.data

    # Sitemap check
    res_sitemap = client.get("/sitemap.xml")
    assert res_sitemap.status_code == 200
    assert b"/projects" in res_sitemap.data
    assert b"/blog" in res_sitemap.data
    assert b"/blog/sitemap-featured-post" in res_sitemap.data
