"""
FILE PURPOSE: Shared pytest fixtures — app/client bound to TestingConfig.

PROMPT FOR LLM IMPLEMENTATION:
1. Before importing the app, set os.environ defaults (via
   os.environ.setdefault) for FLASK_ENV=testing,
   DATABASE_URL=sqlite:///test.db, MAIL_SUPPRESS_SEND=True, SECRET_KEY and
   WTF_CSRF_SECRET_KEY test values — matching docker-compose.test.yml so
   `pytest` behaves identically in and out of Docker.
2. pytest.fixture() named `app`: create_app("testing"), then inside an
   app.app_context() call db.create_all() before yielding the app, and
   db.session.remove() + db.drop_all() after, so every test gets a clean
   database.
3. pytest.fixture() named `client` depending on `app`: returns
   app.test_client().

DEBUGGING:
# print("[DEBUG] conftest — app fixture created")

OFFLINE DOCKER TEST CASES:
- Using the `app` fixture in a trivial test confirms app.testing is True.
- Two tests that each use the `client` fixture don't leak database state
  between each other.
"""
