#!/usr/bin/env bash
# P1-patch.sh
# CodeCrews — Version 2 patch to the already-merged P0/P1 work
#
# Developer: Abhishek (Team Lead and sole developer)
#
# WHY THIS EXISTS (plain language):
# Version 2 adds a second kind of login (coders) next to the single
# super-admin. P1 was written when only the admin existed, so a few P1
# pieces must change BEFORE the coder work (P7) is built:
#   1. Login ids must say which kind of user they belong to ("admin:..." or
#      "coder:...") so the app never mixes the two up.
#   2. Admin pages must check "is this the super-admin?" and not just
#      "is someone logged in?".
#   3. Signed-link helpers (password reset, invites, email verification)
#      move into one shared file.
#   4. Config and .env gain the new settings (private upload folder,
#      token lifetimes, alert batch size).
#
# This script contains zero application logic. Every .py/.yml file below
# is a heredoc holding a PROMPT for an LLM (code-implementer) to fill in.
# .env.example is a static manifest and is written with its final contents.
#
# Run this on MAIN after P1 is merged and BEFORE P2.sh.
# Source docs: technical-design-report-v2.md §6, §15; PDR v2 §5.2.

set -e

echo "====================================================="
echo "CodeCrews — P1 v2 Patch (namespaced logins + role guards)"
echo "Developer: Abhishek"
echo "====================================================="

echo ""
echo "--- Initializing patch branches from MAIN ---"
git checkout MAIN
git pull origin MAIN || echo "WARNING: could not pull MAIN (offline — continuing)."

if git show-ref --quiet refs/heads/phase1-v2-patch-seed; then
    echo "phase1-v2-patch-seed already exists — skipping."
else
    git checkout -b phase1-v2-patch-seed MAIN
fi
if git show-ref --quiet refs/heads/phase1-v2-patch; then
    echo "phase1-v2-patch already exists — skipping."
else
    git checkout -b phase1-v2-patch phase1-v2-patch-seed
fi
git push -u origin phase1-v2-patch-seed || echo "WARNING: could not push phase1-v2-patch-seed."
git push -u origin phase1-v2-patch || echo "WARNING: could not push phase1-v2-patch."

git checkout phase1-v2-patch
mkdir -p app/security app/services tests
git add -A
git commit -q -m "P1-patch: skeleton verification" || echo "Nothing to commit."
git push origin phase1-v2-patch || echo "WARNING: could not push phase1-v2-patch."

echo ""
echo "--- Creating task-abhishek-phase1-v2-patch ---"
git checkout -b task-abhishek-phase1-v2-patch phase1-v2-patch

cat << 'EOF' > .env.example
# Core
SECRET_KEY=change-me-to-a-random-secret
FLASK_ENV=development            # development | testing | production
DATABASE_URL=sqlite:///dev.db    # or postgresql://user:pass@host:5432/codecrews

# Mail
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@codecrews.example
MAIL_SUPPRESS_SEND=False         # set True in docker-compose.test.yml
ADMIN_NOTIFICATION_EMAIL=admin@codecrews.example

# Uploads
UPLOAD_FOLDER=app/static/uploads                 # public media only
PRIVATE_UPLOAD_FOLDER=instance/private_uploads   # request attachments + applicant resumes (never served statically)
MAX_CONTENT_LENGTH=5242880       # 5MB

# Session / security
SESSION_COOKIE_SECURE=False      # True in production
WTF_CSRF_SECRET_KEY=change-me-too
CODER_SESSION_HOURS=8

# Token lifetimes (seconds)
RESET_TOKEN_MAX_AGE=3600
INVITE_TOKEN_MAX_AGE=259200
APPLICATION_VERIFY_MAX_AGE=604800
INTERESTED_TOKEN_MAX_AGE=2592000

# Coder applications / alerts
ALERT_BATCH_SIZE=100
UNVERIFIED_APPLICATION_TTL_DAYS=30

# Seed (used only by seed.py, never read at runtime)
ADMIN_SEED_USERNAME=admin
ADMIN_SEED_PASSWORD=change-me-before-running-seed
EOF

cat << 'EOF' > app/models/admin_user.py
"""
FILE PURPOSE: AdminUser model — Version 2 patch: add a role label and a
namespaced login id so admin and coder sessions can never be confused
(TDR v2 §4 admin_users, §6 "Two user classes, one current_user").

PROMPT FOR LLM IMPLEMENTATION:
1. Keep every column and behavior the P1 version already has (id UUID
   String(36), username unique, password_hash, created_at, UserMixin).
2. Add a class attribute role = "super_admin".
3. Override get_id(self) to return f"admin:{self.id}" (a string). This
   replaces UserMixin's default so Flask-Login stores a prefixed id.
4. Do NOT add any columns — no migration is needed for this change.
5. Keep __repr__ as "<AdminUser {self.username}>".

DEBUGGING:
# print(f"[DEBUG] AdminUser.get_id -> admin:{self.id}")

OFFLINE DOCKER TEST CASES:
- AdminUser(...).role == "super_admin".
- After db.session.add + commit, admin.get_id() == f"admin:{admin.id}".
- Existing P1 behavior (unique username, password_hash round trip) still passes.
"""
EOF

cat << 'EOF' > app/services/tokens.py
"""
FILE PURPOSE: One shared place for every signed, time-limited link the app
emails out (TDR v2 §6 signed tokens table). Replaces the inline
URLSafeTimedSerializer code that P1's auth.py used for password reset.

PROMPT FOR LLM IMPLEMENTATION:
1. Import URLSafeTimedSerializer, BadSignature, SignatureExpired from
   itsdangerous; current_app from flask; hashlib.
2. Define SALTS = {"admin_reset": "admin-reset", "coder_invite":
   "coder-invite", "coder_reset": "coder-reset", "app_verify":
   "app-verify", "app_unsub": "app-unsub", "alert_interest":
   "alert-interest"}.
3. def _serializer(): return URLSafeTimedSerializer(
   current_app.config["SECRET_KEY"]).
4. def fingerprint(password_hash): return hashlib.sha256(
   (password_hash or "").encode()).hexdigest()[:16].
5. def make_token(purpose, payload): returns _serializer().dumps(payload,
   salt=SALTS[purpose]). Raise KeyError for an unknown purpose.
6. def read_token(purpose, token, max_age=None): returns the payload, or
   None when the token is invalid (BadSignature) or expired
   (SignatureExpired). Never raises for bad input. max_age None means
   "no expiry check" (used only for unsubscribe links).
7. def max_age_for(purpose): read the matching config value
   (RESET_TOKEN_MAX_AGE for admin_reset and coder_reset,
   INVITE_TOKEN_MAX_AGE for coder_invite, APPLICATION_VERIFY_MAX_AGE for
   app_verify, INTERESTED_TOKEN_MAX_AGE for alert_interest, None for
   app_unsub).
8. Reset and invite payloads are dicts {"id": ..., "fp": fingerprint(...)}
   built by the caller; this module only signs and reads them.

DEBUGGING:
# print(f"[DEBUG] tokens.make_token purpose={purpose}")
# print(f"[DEBUG] tokens.read_token purpose={purpose} ok={payload is not None}")

OFFLINE DOCKER TEST CASES:
- make_token then read_token with the same purpose returns the payload.
- A token made for "admin_reset" is rejected (None) when read as
  "coder_reset" (salts differ).
- A tampered token returns None, not an exception.
- A token read with max_age=0 after a short sleep returns None (expired).
- fingerprint("a") != fingerprint("b") and is 16 characters long.
"""
EOF

cat << 'EOF' > app/security/__init__.py
"""
FILE PURPOSE: Marks app/security as a package (role guards live here).

PROMPT FOR LLM IMPLEMENTATION:
1. Module docstring only: explain that decorators.py holds
   super_admin_required and coder_required.
2. No imports or logic.

DEBUGGING:
# print("[DEBUG] app.security package imported")

OFFLINE DOCKER TEST CASES:
- `import app.security` does not raise.
"""
EOF

cat << 'EOF' > app/security/decorators.py
"""
FILE PURPOSE: Role guards for the two protected areas (TDR v2 §6 "Role
decorators"). The check is "is this the RIGHT KIND of user", not merely
"is someone logged in".

PROMPT FOR LLM IMPLEMENTATION:
1. Import wraps, current_user, redirect, url_for, abort, request, flash
   from flask / flask_login.
2. def super_admin_required(view): wraps the view. If
   not current_user.is_authenticated -> redirect to url_for("auth.login",
   next=request.path). If authenticated but
   getattr(current_user, "role", None) != "super_admin" -> abort(403).
   Otherwise call the view.
3. def coder_required(view): same shape. Unauthenticated -> redirect to
   url_for("coder_auth.login") (this endpoint does not exist until P7 —
   guard with a try/except BuildError that falls back to
   url_for("auth.login")). Authenticated but role != "coder" -> abort(403).
4. def apply_guard_to_blueprint(blueprint, guard, allow_endpoints=()):
   registers blueprint.before_request that returns None for endpoints in
   allow_endpoints (login, forgot/reset, accept-invite) and otherwise runs
   the guard logic, so a newly added route cannot be accidentally public
   (TDR v2 §6). Endpoints are compared as the part after "blueprint.".
5. Keep every function free of database queries — role is a class
   attribute on the user object.

DEBUGGING:
# print(f"[DEBUG] guard blocked role={getattr(current_user,'role',None)} path={request.path}")

OFFLINE DOCKER TEST CASES:
- Anonymous GET on a guarded route -> 302 to the login page.
- A logged-in user whose role is the wrong one -> 403.
- A route listed in allow_endpoints stays reachable when anonymous.
"""
EOF

cat << 'EOF' > app/routes/auth.py
"""
FILE PURPOSE: Admin auth blueprint — Version 2 patch: namespaced login ids
and shared token helpers (PDR v2 §5.2, TDR v2 §6).

PROMPT FOR LLM IMPLEMENTATION:
1. Keep every route P1 already built (login, logout, forgot-password,
   reset-password/<token>), the rate limit on login, and the generic
   "if that account exists" flash message.
2. Replace the user_loader with a namespaced one: load_user(user_id) splits
   on the first ":"; prefix "admin" -> AdminUser.query.get(rest); prefix
   "coder" -> try to import CoderUser from app.models.coder_user and, if
   the module does not exist yet (before P7), return None; unknown prefix
   or missing row -> None. For coders (P7) it must also return None unless
   status == "active".
3. In login(): before calling login_user(admin) call logout_user() first,
   so one browser holds only one identity.
4. Replace inline URLSafeTimedSerializer code with app.services.tokens:
   make_token("admin_reset", {"id": admin.id, "fp": fingerprint(
   admin.password_hash)}) when issuing; read_token("admin_reset", token,
   max_age_for("admin_reset")) when consuming, and also reject the token
   if the stored fingerprint no longer matches (so a reset link works once).
5. Raise the minimum password length in ResetPasswordForm usage to 10
   characters (the form itself is updated below in this task if needed).
6. url_prefix stays "/admin".

DEBUGGING:
# print(f"[DEBUG] load_user id={user_id!r}")
# print("[DEBUG] reset token fingerprint mismatch -> rejected")

OFFLINE DOCKER TEST CASES:
- POST /admin/login with the seeded admin still redirects to the dashboard.
- The session cookie value stores an id beginning "admin:" (inspect
  session["_user_id"] in a test request context).
- A reset link used once cannot be used a second time.
- load_user("coder:xyz") returns None before CoderUser exists.
- load_user("nonsense") returns None without raising.
"""
EOF

cat << 'EOF' > app/forms/auth_forms.py
"""
FILE PURPOSE: Flask-WTF forms for the admin auth flow — Version 2 patch:
stronger minimum password length.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep LoginForm, ForgotPasswordForm, ResetPasswordForm exactly as P1
   defined them.
2. Change ResetPasswordForm.password Length(min=8) to Length(min=10) and
   update the error message to say "at least 10 characters".

DEBUGGING:
# print("[DEBUG] auth_forms — ResetPasswordForm min length is 10")

OFFLINE DOCKER TEST CASES:
- ResetPasswordForm with a 9-character password fails validation.
- ResetPasswordForm with a 10-character matching pair passes.
"""
EOF

cat << 'EOF' > app/routes/admin.py
"""
FILE PURPOSE: Admin blueprint — Version 2 patch: switch from "any logged-in
user" to "super-admin only".

PROMPT FOR LLM IMPLEMENTATION:
1. Keep the existing dashboard route and url_prefix "/admin".
2. Replace @login_required on dashboard() with @super_admin_required
   (from app.security.decorators).
3. After creating admin_bp, call apply_guard_to_blueprint(admin_bp,
   super_admin_required) so every route added in later milestones is
   guarded automatically.
4. Do not add any other routes.

DEBUGGING:
# print("[DEBUG] admin_bp guarded by super_admin_required")

OFFLINE DOCKER TEST CASES:
- Anonymous GET /admin/dashboard -> 302 to /admin/login.
- Logged-in admin GET /admin/dashboard -> 200.
- A fake logged-in user object with role "coder" gets 403.
"""
EOF

cat << 'EOF' > app/config.py
"""
FILE PURPOSE: Environment-driven config classes — Version 2 patch: new
settings for private uploads, token lifetimes, coder sessions, alerts.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything P0 already defines (Dev/Testing/Production classes,
   get_config, existing settings).
2. Add to BaseConfig (all from os.environ with these defaults):
   PRIVATE_UPLOAD_FOLDER="instance/private_uploads";
   CODER_SESSION_HOURS=8 (int); RESET_TOKEN_MAX_AGE=3600;
   INVITE_TOKEN_MAX_AGE=259200; APPLICATION_VERIFY_MAX_AGE=604800;
   INTERESTED_TOKEN_MAX_AGE=2592000; ALERT_BATCH_SIZE=100;
   UNVERIFIED_APPLICATION_TTL_DAYS=30 (all ints).
3. TestingConfig: PRIVATE_UPLOAD_FOLDER default "instance/test_private_uploads".
4. Keep UPLOAD_FOLDER as the PUBLIC media folder only (comment this).

DEBUGGING:
# print(f"[DEBUG] config private folder: {PRIVATE_UPLOAD_FOLDER}")

OFFLINE DOCKER TEST CASES:
- get_config("testing")().ALERT_BATCH_SIZE == 100.
- get_config("testing")().PRIVATE_UPLOAD_FOLDER differs from UPLOAD_FOLDER.
- Setting INVITE_TOKEN_MAX_AGE in the environment overrides the default.
"""
EOF

cat << 'EOF' > docker-compose.yml
# FILE PURPOSE: Local dev orchestration — Version 2 patch: private upload
# volume.
#
# PROMPT FOR LLM IMPLEMENTATION:
# 1. Keep the P0 definition (web + db services, env_file, ports).
# 2. Add a named volume `private_uploads` mounted into the web service at
#    /code/instance/private_uploads so confidential request attachments and
#    applicant resumes survive container rebuilds.
# 3. Declare `private_uploads` under the top-level `volumes:` key.
# 4. Add a comment: this folder must never be served as static files.
#
# DEBUGGING:
# # command: sh -c "ls -la instance/private_uploads"
#
# OFFLINE DOCKER TEST CASES:
# - `docker-compose config` parses without error.
# - A file written to instance/private_uploads inside the container is
#   still present after `docker-compose down` and `up`.
EOF

cat << 'EOF' > tests/test_role_guards.py
"""
FILE PURPOSE: Acceptance tests for the Version 2 patch.

PROMPT FOR LLM IMPLEMENTATION:
1. test_admin_session_id_is_namespaced(logged_in_client): after login, read
   the session's "_user_id" and assert it starts with "admin:".
2. test_dashboard_still_requires_login(client): GET /admin/dashboard
   returns 302 to /admin/login.
3. test_wrong_role_gets_403(app): register a throwaway guarded route on a
   test blueprint using super_admin_required; log in a minimal fake user
   object whose role is "coder" (via a test-only user_loader override);
   assert 403.
4. test_tokens_round_trip_and_purpose_isolation(app): in an app context,
   make_token("admin_reset", {"id": "1"}) reads back correctly and is
   rejected when read with purpose "coder_reset".
5. test_reset_token_single_use(client, admin_user): request a reset, use
   the token to set a new password, then try the same token again and
   assert it is rejected.
6. test_all_models_registered still passes (carried over from P1).

DEBUGGING:
# print("[DEBUG] running v2 patch role-guard tests")

OFFLINE DOCKER TEST CASES:
- All six tests pass with zero network access and MAIL_SUPPRESS_SEND=True.
"""
EOF

git add -A
git commit -q -m "P1-patch seed: namespaced logins, role guards, shared tokens, config (Abhishek)"
git push -u origin task-abhishek-phase1-v2-patch || echo "WARNING: could not push task-abhishek-phase1-v2-patch."

echo ""
echo "====================================================="
echo "P1 v2 patch seeded on task-abhishek-phase1-v2-patch."
echo "NEXT STEPS (Abhishek):"
echo "1. Feed the seeded files to your LLM (code-implementer) to generate the code."
echo "2. Run: docker-compose -f docker-compose.test.yml run --rm web pytest"
echo "3. Open a PR into 'phase1-v2-patch', review, merge it, then merge to MAIN and tag v2-patch."
echo "4. Execute P2.sh."
echo "====================================================="
