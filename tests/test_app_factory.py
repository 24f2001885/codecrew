"""
FILE PURPOSE: P0 acceptance tests — matches the Master Project
Blueprint's P0 Goal verbatim. Depends on Abhinav's app factory, Piyush's
model stubs, and Harshlata's templates all being merged into the branch
under test.

PROMPT FOR LLM IMPLEMENTATION:
1. test_app_factory_creates_app_in_testing_mode(app): assert app.testing
   is True and app.config["SQLALCHEMY_DATABASE_URI"] starts with
   "sqlite:///test".
2. test_index_returns_200(client): GET "/" returns status_code 200.
3. test_index_contains_loader_navbar_and_footer(client): GET "/" body
   contains 'id="ftco-loader"', 'id="ftco-navbar"', "<footer", and all
   four nav labels ("Home", "Groups", "Our Members", "Request a Project").
4. test_all_stub_models_are_registered(app): within an app context,
   assert {"admin_users","groups","members","projects","blog_posts",
   "contact_messages","project_requests","site_settings"} is a subset of
   db.metadata.tables.keys().

DEBUGGING:
# print("[DEBUG] running P0 acceptance tests")

OFFLINE DOCKER TEST CASES:
- All four tests above pass with zero network access, entirely against
  the SQLite test database created by conftest.py, once all four task
  branches are integrated into phase0.
"""
