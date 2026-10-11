import csv
import io
import pytest
from app.extensions import db, mail
from app.models.group import Group
from app.models.member import Member
from app.models.project_request import ProjectRequest
from app.models.coder_application import CoderApplication
from app.services.mailer import send_application_verify, send_coder_invite, send_domain_alert


def test_sitemap_xml(client, app):
    with app.app_context():
        g = Group(name="Sitemap Squad", slug="sitemap-squad")
        db.session.add(g)
        db.session.commit()

    res = client.get("/sitemap.xml")
    assert res.status_code == 200
    assert "application/xml" in res.content_type
    assert b"<urlset" in res.data
    assert b"/group/sitemap-squad" in res.data
    assert b"/request-project" in res.data


def test_robots_txt(client):
    res = client.get("/robots.txt")
    assert res.status_code == 200
    assert "text/plain" in res.content_type
    assert b"Disallow: /admin/" in res.data
    assert b"Disallow: /coder/" in res.data
    assert b"Sitemap:" in res.data


def test_csv_exports_access_control(client):
    # Unauthenticated requests must be blocked
    res1 = client.get("/admin/export/requests.csv")
    assert res1.status_code == 302
    assert "/admin/login" in res1.location

    res2 = client.get("/admin/export/applications.csv")
    assert res2.status_code == 302

    res3 = client.get("/admin/export/members.csv")
    assert res3.status_code == 302


def test_csv_exports_data(logged_in_client, app):
    with app.app_context():
        g = Group(name="Export Crew", slug="export-crew")
        db.session.add(g)
        db.session.flush()

        m = Member(name="Export Dev", role="Lead Dev", group_id=g.id)
        db.session.add(m)

        pr = ProjectRequest(
            name="Requester One",
            email="req1@test.com",
            company="Company A",
            project_type="web_app",
            budget_range="$10k",
            timeline="1 month",
            description="Build app",
        )
        db.session.add(pr)

        ca = CoderApplication(
            name="Applicant One",
            email="app1@test.com",
            project_types=["web_app"],
            domain_tags=["python", "flask"],
            status="pending",
        )
        db.session.add(ca)
        db.session.commit()

    # Test Project Requests CSV
    res_pr = logged_in_client.get("/admin/export/requests.csv")
    assert res_pr.status_code == 200
    assert "text/csv" in res_pr.content_type
    pr_csv = res_pr.data.decode("utf-8")
    assert "Requester One" in pr_csv
    assert "req1@test.com" in pr_csv

    # Test Applications CSV
    res_ca = logged_in_client.get("/admin/export/applications.csv")
    assert res_ca.status_code == 200
    assert "text/csv" in res_ca.content_type
    ca_csv = res_ca.data.decode("utf-8")
    assert "Applicant One" in ca_csv
    assert "app1@test.com" in ca_csv

    # Test Members CSV
    res_m = logged_in_client.get("/admin/export/members.csv")
    assert res_m.status_code == 200
    assert "text/csv" in res_m.content_type
    m_csv = res_m.data.decode("utf-8")
    assert "Export Dev" in m_csv
    assert "Export Crew" in m_csv


def test_branded_html_emails(app):
    with app.app_context():
        ca = CoderApplication(
            name="Email Test Applicant",
            email="testapplicant@example.com",
            project_types=["web_app"],
        )
        db.session.add(ca)
        db.session.commit()

        with mail.record_messages() as outbox:
            send_application_verify(ca, "https://codecrews.example/verify/dummy")
            assert len(outbox) == 1
            msg = outbox[0]
            assert "Verify Your Email" in msg.subject
            assert "https://codecrews.example/verify/dummy" in msg.body
            # Check HTML attachment
            assert msg.html is not None
            assert "Verify Email Address" in msg.html
            assert "CODE<span style=\"color: #f59e0b;\">CREWS</span>" in msg.html
