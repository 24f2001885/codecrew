from datetime import datetime
import pytest
from app.extensions import db
from app.models.group import Group
from app.models.blog_post import BlogPost


@pytest.fixture
def blog_group(app):
    with app.app_context():
        g1 = Group(name="Cyber Security Squad", slug="cyber-security-squad")
        g2 = Group(name="Cloud Titans", slug="cloud-titans")
        db.session.add_all([g1, g2])
        db.session.commit()
        return g1.id, g2.id


def test_blog_requires_admin_login(client):
    # Anonymous request gets 302 to login
    resp = client.get("/admin/blog")
    assert resp.status_code == 302
    assert "/admin/login" in resp.headers["Location"]


def test_create_published_post_appears_on_group_page_only(logged_in_client, app, blog_group):
    g1_id, g2_id = blog_group
    post_data = {
        "group_id": g1_id,
        "title": "Securing Flask Applications with CSRF",
        "content": "This is a comprehensive guide to protecting Flask routes with CSRF tokens and secure session management.",
        "tags": "security, flask, python",
        "published": "y",
    }
    resp = logged_in_client.post("/admin/blog/new", data=post_data, follow_redirects=True)
    assert resp.status_code == 200
    assert b"created successfully" in resp.data

    with app.app_context():
        post = BlogPost.query.filter_by(title="Securing Flask Applications with CSRF").first()
        assert post is not None
        assert post.group_id == g1_id
        assert post.is_published is True
        assert post.published_at is not None

    # Appears on Cyber Security Squad page
    pub_resp1 = logged_in_client.get("/group/cyber-security-squad")
    assert pub_resp1.status_code == 200
    assert b"Securing Flask Applications with CSRF" in pub_resp1.data
    assert b"Dev Log" in pub_resp1.data

    # Does NOT appear on Cloud Titans page
    pub_resp2 = logged_in_client.get("/group/cloud-titans")
    assert pub_resp2.status_code == 200
    assert b"Securing Flask Applications with CSRF" not in pub_resp2.data


def test_draft_hidden_from_public(logged_in_client, app, blog_group):
    g1_id, _ = blog_group
    draft_data = {
        "group_id": g1_id,
        "title": "Unpublished Draft Research Notes",
        "content": "Secret draft notes that are currently work in progress and not ready for release.",
        "tags": "research, draft",
        # published omitted / unchecked
    }
    resp = logged_in_client.post("/admin/blog/new", data=draft_data, follow_redirects=True)
    assert resp.status_code == 200

    with app.app_context():
        post = BlogPost.query.filter_by(title="Unpublished Draft Research Notes").first()
        assert post is not None
        assert post.is_published is False
        assert post.published_at is None

    # Must NOT appear on public group page
    pub_resp = logged_in_client.get("/group/cyber-security-squad")
    assert pub_resp.status_code == 200
    assert b"Unpublished Draft Research Notes" not in pub_resp.data


def test_slug_unique_within_group_only(logged_in_client, app, blog_group):
    g1_id, g2_id = blog_group

    # Two posts in the SAME group with identical titles
    p1_data = {
        "group_id": g1_id,
        "title": "Kubernetes Architecture",
        "content": "Detailed overview of k8s cluster orchestration and networking.",
    }
    logged_in_client.post("/admin/blog/new", data=p1_data, follow_redirects=True)

    p2_data = {
        "group_id": g1_id,
        "title": "Kubernetes Architecture",
        "content": "Another deep dive into k8s architecture in group 1.",
    }
    logged_in_client.post("/admin/blog/new", data=p2_data, follow_redirects=True)

    # Post in a DIFFERENT group with the same title
    p3_data = {
        "group_id": g2_id,
        "title": "Kubernetes Architecture",
        "content": "Kubernetes architecture from group 2's perspective.",
    }
    logged_in_client.post("/admin/blog/new", data=p3_data, follow_redirects=True)

    with app.app_context():
        g1_posts = BlogPost.query.filter_by(group_id=g1_id, title="Kubernetes Architecture").all()
        assert len(g1_posts) == 2
        slugs_g1 = {p.slug for p in g1_posts}
        assert "kubernetes-architecture" in slugs_g1
        assert "kubernetes-architecture-2" in slugs_g1

        g2_post = BlogPost.query.filter_by(group_id=g2_id, title="Kubernetes Architecture").first()
        assert g2_post.slug == "kubernetes-architecture"  # Keeps clean plain slug in other group


def test_group_id_required(logged_in_client, app):
    bad_data = {
        "group_id": "",
        "title": "Orphan Blog Post",
        "content": "This post has no assigned group and must fail validation.",
    }
    resp = logged_in_client.post("/admin/blog/new", data=bad_data)
    assert resp.status_code == 200
    assert b"Group is required" in resp.data


def test_delete_is_post_only_and_cascades_with_group_delete(logged_in_client, app, blog_group):
    g1_id, _ = blog_group
    with app.app_context():
        p = BlogPost(
            group_id=g1_id,
            title="Post To Be Deleted",
            slug="post-to-be-deleted",
            content="Testing deletion mechanics for blog posts.",
        )
        db.session.add(p)
        db.session.commit()
        pid = p.id

    # GET is 405 Method Not Allowed
    get_resp = logged_in_client.get(f"/admin/blog/{pid}/delete")
    assert get_resp.status_code == 405

    # POST deletes post
    post_resp = logged_in_client.post(f"/admin/blog/{pid}/delete", follow_redirects=True)
    assert post_resp.status_code == 200
    assert b"deleted" in post_resp.data

    with app.app_context():
        assert db.session.get(BlogPost, pid) is None

    # Test cascade: deleting the group deletes all its posts
    with app.app_context():
        p2 = BlogPost(
            group_id=g1_id,
            title="Cascade Post",
            slug="cascade-post",
            content="Should be removed when group is deleted.",
        )
        db.session.add(p2)
        db.session.commit()
        p2_id = p2.id

    del_grp_resp = logged_in_client.post(f"/admin/groups/{g1_id}/delete", follow_redirects=True)
    assert del_grp_resp.status_code == 200

    with app.app_context():
        assert db.session.get(BlogPost, p2_id) is None


def test_post_content_is_escaped_on_public_page(logged_in_client, app, blog_group):
    g1_id, _ = blog_group
    xss_payload = "<script>alert('xss')</script>"
    with app.app_context():
        p = BlogPost(
            group_id=g1_id,
            title="Testing Script Escaping",
            slug="testing-script-escaping",
            content=f"Paragraph 1 containing {xss_payload}\n\nParagraph 2 safely rendered.",
            published_at=datetime.utcnow(),
        )
        db.session.add(p)
        db.session.commit()

    pub_resp = logged_in_client.get("/group/cyber-security-squad")
    assert pub_resp.status_code == 200
    # Must NOT have unescaped raw tag
    assert b"<script>alert('xss')</script>" not in pub_resp.data
    # Escaped HTML entities must be present
    assert b"&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;" in pub_resp.data or b"&lt;script&gt;" in pub_resp.data
