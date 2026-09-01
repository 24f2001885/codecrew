"""
FILE PURPOSE: Database seed CLI — full logic per PDR §5.2 / TDR §13's
operational runbook. Creates the single super-admin row and nothing
else in P1 (sample Groups/Members/Projects arrive as fixture data in
P2, not here).

PROMPT FOR LLM IMPLEMENTATION:
1. Import create_app from app, db from app.extensions, AdminUser from
   app.models.admin_user, generate_password_hash from
   werkzeug.security, and os.
2. Define run(): builds the app via create_app(), enters an
   app.app_context().
3. Read ADMIN_SEED_USERNAME and ADMIN_SEED_PASSWORD from os.environ
   (PDR §5.2: "seeded via a CLI script, never through a UI form"). If
   either is missing, print a clear error and return without writing
   anything (exit 1 via sys.exit(1)).
4. Idempotency check: query AdminUser.query.filter_by(username=...).
   first(). If a row already exists, print "Super-admin '<username>'
   already exists — skipping." and return without creating a duplicate
   (there must only ever be one AdminUser row, per PDR §5.2 / TDR §4).
5. Otherwise, create AdminUser(username=..., password_hash=
   generate_password_hash(password)), db.session.add + commit, and
   print a confirmation (never print the raw password).
6. `if __name__ == "__main__": run()`.

DEBUGGING:
# print(f"[DEBUG] seed.py — ADMIN_SEED_USERNAME={os.environ.get('ADMIN_SEED_USERNAME')!r} (password never logged)")

OFFLINE DOCKER TEST CASES:
- Running `python seed.py` with ADMIN_SEED_USERNAME/PASSWORD set in the
  test environment creates exactly one admin_users row.
- Running it a second time does not create a second row (AdminUser.query.count()
  stays 1) and exits 0.
- Running it with ADMIN_SEED_USERNAME unset exits non-zero and writes no
  rows.
"""
