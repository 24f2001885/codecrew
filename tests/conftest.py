"""
FILE PURPOSE: Shared pytest fixtures — extends the P0 app/client fixtures
with an `admin_user` fixture and a `logged_in_client` fixture, since
every P1 auth test needs a real seeded admin row and an authenticated
session.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep the existing `app` and `client` fixtures from P0 exactly as they
   are (os.environ.setdefault for testing config, db.create_all()/
   drop_all() around each test).
2. Add pytest.fixture() named `admin_user` depending on `app`: inside
   the app's context, import AdminUser from app.models.admin_user and
   generate_password_hash from werkzeug.security, create
   AdminUser(username="testadmin",
   password_hash=generate_password_hash("testpassword123")),
   db.session.add + commit, yield the created row (tests need the
   plaintext "testpassword123" too — expose it as a second fixture
   `admin_password` returning the literal string, so tests never need to
   hardcode it twice).
3. Add pytest.fixture() named `logged_in_client` depending on `client`,
   `admin_user`, and `admin_password`: POSTs to "/admin/login" with the
   admin's username + the known plaintext password, asserts the
   response is a redirect (proving login succeeded), then yields the
   same `client` (now holding an authenticated session cookie) for the
   test to reuse.

DEBUGGING:
# print("[DEBUG] conftest — admin_user + logged_in_client fixtures ready")

OFFLINE DOCKER TEST CASES:
- Using `admin_user` in isolation confirms exactly one admin_users row
  exists afterward.
- Using `logged_in_client` in a trivial test and then GETting
  "/admin/dashboard" returns 200 (not a 302 to login).
"""
