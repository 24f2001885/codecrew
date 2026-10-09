import json
import re
from app.extensions import db, limiter
from app.models.group import Group


def test_404_is_themed_and_has_no_traceback(client):
    resp = client.get("/does-not-exist-at-all")
    assert resp.status_code == 404
    html = resp.data.decode("utf-8")
    assert "404" in html
    assert "We can&#39;t find that page" in html or "We can't find that page" in html
    assert "Back to Home" in html
    assert "Browse Groups" in html
    assert "Traceback (most recent call last)" not in html
    assert 'File "' not in html


def test_500_is_themed_and_hides_exception_text(app):
    # Register a route that raises an unhandled exception
    @app.route("/test-raise-internal-error")
    def trigger_error():
        raise RuntimeError("SecretDatabasePasswordLeaksNever")

    app.config["TESTING"] = False
    app.config["PROPAGATE_EXCEPTIONS"] = False
    client = app.test_client()
    resp = client.get("/test-raise-internal-error")
    assert resp.status_code == 500
    html = resp.data.decode("utf-8")
    assert "500" in html
    assert "Something went wrong on our side" in html
    assert "Back to Home" in html
    # Ensure sensitive exception details are hidden
    assert "SecretDatabasePasswordLeaksNever" not in html
    assert "Traceback (most recent call last)" not in html



def test_429_page_for_rate_limited_request(app):
    # Register a route strictly limited to 1 per minute for testing
    @app.route("/test-rate-limit-endpoint")
    @limiter.limit("1 per minute")
    def rate_limited_endpoint():
        return "OK"

    client = app.test_client()
    resp1 = client.get("/test-rate-limit-endpoint")
    assert resp1.status_code == 200

    resp2 = client.get("/test-rate-limit-endpoint")
    assert resp2.status_code == 429
    html = resp2.data.decode("utf-8")
    assert "429" in html
    assert "Too Many Requests" in html
    assert "Back to Home" in html


def test_security_headers_present_on_every_response(client):
    endpoints = ["/", "/groups", "/does-not-exist"]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "Content-Security-Policy" in resp.headers
        csp = resp.headers.get("Content-Security-Policy")
        assert "default-src 'self'" in csp
        assert "style-src 'self' 'unsafe-inline'" in csp


def test_group_page_has_unique_seo_tags_and_valid_jsonld(app, client):
    with app.app_context():
        g1 = Group(name="Alpha Dynamics", slug="alpha-dynamics", tagline="Autonomous AI systems", description="Full squad building AI.")
        g2 = Group(name="Beta Robotics", slug="beta-robotics", tagline="Hardware interfacing", description="Full squad building bots.")
        db.session.add_all([g1, g2])
        db.session.commit()

    resp1 = client.get("/group/alpha-dynamics")
    resp2 = client.get("/group/beta-robotics")
    assert resp1.status_code == 200
    assert resp2.status_code == 200

    html1 = resp1.data.decode("utf-8")
    html2 = resp2.data.decode("utf-8")

    # Titles and og:title must be unique
    assert "Alpha Dynamics — CodeCrews" in html1
    assert "Beta Robotics — CodeCrews" in html2
    assert html1 != html2

    # Extract JSON-LD script from Alpha Dynamics page
    match = re.search(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>', html1, re.DOTALL)
    assert match is not None, "JSON-LD script tag not found"
    json_str = match.group(1)
    data = json.loads(json_str)

    assert data.get("@context") == "https://schema.org"
    assert data.get("@type") == "Organization"
    assert data.get("name") == "Alpha Dynamics"
    assert data.get("description") == "Autonomous AI systems"
