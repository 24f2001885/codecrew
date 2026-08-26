"""
FILE PURPOSE: Public blueprint — P0 scope is a single route proving the
themed shell renders end to end.

PROMPT FOR LLM IMPLEMENTATION:
1. public_bp = Blueprint("public", __name__).
2. @public_bp.route("/") def index(): renders "base.html" directly — no
   real Home page content yet (hero/stats/carousel/directory teaser is
   P2's job per the Master Project Blueprint). NOTE: "base.html" and its
   partials are seeded by Harshlata on task-harshlata-themed-shell.
3. Keep the route free of any database queries — P0 has no seeded data.

DEBUGGING:
# print("[DEBUG] GET / — rendering bare themed shell (P0)")

OFFLINE DOCKER TEST CASES:
- GET "/" returns HTTP 200.
- The response body contains 'id="ftco-loader"', 'id="ftco-navbar"', and
  "<footer" (proving the included partials actually rendered) — verify
  once Harshlata's template branch is merged in.
"""
