#!/usr/bin/env bash
# P1.sh
# CodeCrews — Milestone P1: Data Models & Admin Auth Shell
#
# Team for this milestone:
#   Abhishek  — Team Lead (phase init, PR review/integration,
#               test-phase decision per team_lead_workflow_guide.pdf)
#   Abhinav   — App Core & Wiring (app factory updates, dashboard route, seed.py)
#   Piyush    — Data Models (full column definitions, all 8 tables)
#   Harshlata — Admin Shell (Frontend) (admin_base + login/forgot/reset/dashboard templates)
#   Utkarsh   — Auth & Forms (auth blueprint routes, WTForms, password-reset mailer)
#   Tripti    — Docker & Testing Infra (auth test suite, conftest fixtures)
#
# Source docs: master-project-blueprint.md §1 (dir tree) + §3 (P1 map),
# project-definition-report.md §5.2/§5.1, technical-design-report.md
# §4 (schema) / §5 (auth routes) / §6 (security) / §12 (logging),
# ui-ux-design-plan.md §4.1, developer_workflow_guide.pdf,
# team_lead_workflow_guide.pdf.

set -e

echo "====================================================="
echo "CodeCrews — P1: Data Models & Admin Auth Shell"
echo "Team: Abhishek (Lead), Abhinav, Piyush, Harshlata, Utkarsh, Tripti"
echo "====================================================="

# -----------------------------------------------------------------------
# 1. TEAM LEAD (ABHISHEK) — PHASE INITIALIZATION
# -----------------------------------------------------------------------
echo ""
echo "--- [Abhishek | Team Lead] Phase 1 initialization ---"

git checkout MAIN
git pull origin MAIN || echo "WARNING: could not pull MAIN (offline/new repo — continuing)."

if git show-ref --quiet refs/heads/phase1-seed; then
    echo "phase1-seed already exists locally — skipping creation."
else
    echo "Creating phase1-seed from MAIN..."
    git checkout -b phase1-seed MAIN
fi

if git show-ref --quiet refs/heads/phase1; then
    echo "phase1 already exists locally — skipping creation."
else
    echo "Creating phase1 from phase1-seed..."
    git checkout -b phase1 phase1-seed
fi

echo "Pushing structural branches to origin..."
git push -u origin phase1-seed || echo "WARNING: could not push phase1-seed (check remote access)."
git push -u origin phase1 || echo "WARNING: could not push phase1 (check remote access)."

# -----------------------------------------------------------------------
# 2. TEAM LEAD (ABHISHEK) — DIRECTORY CHECK ON phase1
# -----------------------------------------------------------------------
echo ""
echo "--- [Abhishek | Team Lead] Verifying base skeleton on phase1 ---"
git checkout phase1

mkdir -p app/models app/routes app/forms app/services app/templates/admin migrations tests
touch app/models/.gitkeep app/routes/.gitkeep app/forms/.gitkeep app/services/.gitkeep app/templates/admin/.gitkeep migrations/.gitkeep tests/.gitkeep

git add -A
git commit -q -m "P1: skeleton verification (Abhishek)" || echo "Nothing to commit for skeleton verification."
git push origin phase1 || echo "WARNING: could not push phase1 (check remote access)."

# =========================================================================
# 3. DEVELOPER TASK BRANCHES
# =========================================================================

# -------------------------------------------------------------------
# 3a. ABHINAV — App Core & Wiring
# -------------------------------------------------------------------
echo ""
echo "--- [Abhinav] Syncing phase1 and creating task-abhinav-phase1-app-core ---"
git checkout phase1
git pull origin phase1 || echo "WARNING: could not pull phase1 (offline/new repo — continuing)."
git checkout -B task-abhinav-phase1-app-core phase1

mkdir -p app/routes

cat << 'EOF' > app/__init__.py
"""
FILE PURPOSE: Flask application factory — extends the P0 skeleton to
register the new auth blueprint, gate the first admin route, and confirm
every full model (Piyush's task-piyush-phase1-data-models branch) is
visible to Flask-Migrate.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything create_app() already does in P0 (config load, extension
   init, model imports inside an app context, logging setup, `now`
   context processor).
2. _register_blueprints(app): now also import and register `auth_bp` from
   app/routes/auth.py and a new `admin_bp` from app/routes/admin.py,
   alongside the existing `public_bp`. Leave a comment noting the
   remaining admin CRUD blueprints (contact_bp/requests_bp in P4,
   api_bp in P5) still aren't registered yet.
3. Confirm login_manager.init_app(app) is called (it already is, from
   app/extensions.py) and that AdminUser is importable at the point
   login_manager's user_loader callback (defined in app/routes/auth.py)
   needs it — this only works once Piyush's branch is merged into
   phase1, note that as a comment.
4. No other changes to the factory's shape from P0.

DEBUGGING:
# print(f"[DEBUG] App created with config={config_name}; blueprints=public,auth,admin")

OFFLINE DOCKER TEST CASES:
- create_app("testing") still returns a Flask instance with app.testing
  is True.
- GET "/admin/dashboard" without a session redirects (302) to
  "/admin/login" (proves @login_required + login_manager.login_view
  wiring from app/extensions.py actually took effect).
- GET "/admin/login" returns HTTP 200 once Harshlata's login.html and
  Utkarsh's auth routes are merged in.
"""
EOF

cat << 'EOF' > app/routes/admin.py
"""
FILE PURPOSE: Admin blueprint — P1 scope is exactly one route (the empty
Dashboard) proving the @login_required gate and admin_base.html shell
render end to end. Full CRUD screens are P3+ scope (Master Project
Blueprint §3).

PROMPT FOR LLM IMPLEMENTATION:
1. admin_bp = Blueprint("admin", __name__, url_prefix="/admin").
2. @admin_bp.route("/dashboard") def dashboard(): decorate with
   @login_required (from flask_login), render "admin/dashboard.html".
   NOTE: "admin/dashboard.html" and "admin/admin_base.html" are seeded by
   Harshlata on task-harshlata-phase1-admin-shell.
3. Do NOT add any Group/Member/Project/Message/Request summary-card
   queries yet — those models have no seeded rows until P2/P3, and the
   Dashboard is explicitly "empty" per the Blueprint's P1 goal. Pass no
   extra template context beyond what admin_base.html needs.
4. Keep this file free of any CRUD routes — Groups/Members/Projects/Blog/
   Messages/Project Requests/Settings routes all land on this same
   blueprint later (P3, P4, P6) per the Unified Directory Structure.

DEBUGGING:
# print("[DEBUG] GET /admin/dashboard — rendering empty admin shell (P1)")

OFFLINE DOCKER TEST CASES:
- GET "/admin/dashboard" with no session redirects to "/admin/login".
- GET "/admin/dashboard" with a logged-in test session (via Utkarsh's
  auth routes) returns HTTP 200 and includes the admin sidebar markup
  from admin_base.html.
"""
EOF

cat << 'EOF' > seed.py
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
EOF

git add -A
git commit -q -m "P1 seed: app core & wiring placeholders (Abhinav)"
git push -u origin task-abhinav-phase1-app-core -f || echo "WARNING: could not push task-abhinav-phase1-app-core (check remote access)."

# -------------------------------------------------------------------
# 3b. PIYUSH — Data Models
# -------------------------------------------------------------------
echo ""
echo "--- [Piyush] Syncing phase1 and creating task-piyush-phase1-data-models ---"
git checkout phase1
git pull origin phase1 || echo "WARNING: could not pull phase1 (offline/new repo — continuing)."
git checkout -B task-piyush-phase1-data-models phase1

mkdir -p app/models

cat << 'EOF' > app/models/admin_user.py
"""
FILE PURPOSE: AdminUser model — full columns (TDR §4 table: admin_users).
Also needs to satisfy Flask-Login's UserMixin contract, since
login_manager (app/extensions.py) authenticates against this model.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions, and
   UserMixin from flask_login.
2. class AdminUser(db.Model, UserMixin) with __tablename__ = "admin_users".
3. Columns exactly per TDR §4: id (String(36) UUID PK, default
   lambda: str(uuid.uuid4())); username (String(80), unique, not null);
   password_hash (String(255), not null); created_at (DateTime, not
   null, default datetime.now(timezone.utc)).
4. UserMixin gives get_id()/is_authenticated/etc for free — since id is
   already a string, no override needed.
5. __repr__ returning "<AdminUser {self.username}>".

DEBUGGING:
# print(f"[DEBUG] AdminUser stub -> full model registered: {AdminUser.__tablename__}")

OFFLINE DOCKER TEST CASES:
- AdminUser(username="admin", password_hash="x").get_id() returns the
  row's UUID string once persisted (id is not None after db.session.add
  + commit + refresh).
- AdminUser.query.filter_by(username="admin").first() round-trips
  correctly after seed.py creates a row.
- The `username` column rejects a duplicate value at the DB level
  (unique constraint) when two rows share a username.
"""
EOF

cat << 'EOF' > app/models/group.py
"""
FILE PURPOSE: Group model — full columns (TDR §4 table: groups), the
central entity of the platform. Relationships to Member/Project/
BlogPost/ContactMessage/ProjectRequest are declared here since Group is
the "one" side of every one-to-many in the schema.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions.
2. class Group(db.Model) with __tablename__ = "groups".
3. Columns exactly per TDR §4: id (UUID PK); name (String(120), not
   null); slug (String(140), unique, not null, indexed); tagline
   (String(200), nullable); description (Text, nullable); logo_path
   (String(255), nullable); cover_image_path (String(255), nullable);
   founded_date (Date, nullable); location (String(120), nullable);
   tech_tags (JSON, not null, default list); social_links (JSON, not
   null, default dict); featured (Boolean, not null, default False);
   created_at / updated_at (DateTime, not null, default now, updated_at
   also on-update now).
4. Relationships: members = db.relationship("Member", backref="group",
   cascade="all, delete-orphan"); projects = db.relationship("Project",
   backref="group", cascade="all, delete-orphan"); blog_posts =
   db.relationship("BlogPost", backref="group", cascade="all,
   delete-orphan"); contact_messages = db.relationship("ContactMessage",
   backref="group", cascade="all, delete-orphan") — matching the FK
   ON DELETE CASCADE behavior specified in TDR §4/§5 (deleting a group
   cascades to its members/projects/blog/messages).
5. __repr__ returning "<Group {self.name}>".

DEBUGGING:
# print(f"[DEBUG] Group full model registered: {Group.__tablename__}")

OFFLINE DOCKER TEST CASES:
- A Group's `tech_tags` and `social_links` default to [] and {}
  respectively when not explicitly set at construction time.
- Deleting a Group cascades to its related Member/Project rows in a
  round-trip test (create group + member, delete group, assert member
  row is also gone).
- `slug` rejects a duplicate value at the DB level.
"""
EOF

cat << 'EOF' > app/models/member.py
"""
FILE PURPOSE: Member model — full columns (TDR §4 table: members),
including the v2-added resume_pdf field (PDR §5.4).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions.
2. class Member(db.Model) with __tablename__ = "members".
3. Columns exactly per TDR §4: id (UUID PK); group_id (String(36) FK ->
   groups.id, not null, indexed, ondelete="CASCADE"); name
   (String(120), not null); role (String(120), nullable); photo_path
   (String(255), nullable); bio (Text, nullable); skill_tags (JSON, not
   null, default list); github_url / linkedin_url / twitter_url
   (String(255), nullable each); resume_pdf (String(255), nullable —
   "added in v2" per TDR §4); display_order (Integer, not null, default
   0); created_at (DateTime, not null, default now).
4. No explicit relationship() declared here — Group.members (backref)
   from group.py already provides the reverse side.
5. __repr__ returning "<Member {self.name}>".

DEBUGGING:
# print(f"[DEBUG] Member full model registered: {Member.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Member.skill_tags defaults to [] when not set at construction.
- A Member with resume_pdf=None round-trips correctly (nullable, not
  required — PDR §5.4: uploads are opt-in per member).
- Creating a Member with a group_id that doesn't exist in `groups`
  raises an IntegrityError (FK enforcement) once SQLite foreign_keys
  pragma / Postgres FK is active.
"""
EOF

cat << 'EOF' > app/models/project.py
"""
FILE PURPOSE: Project model — full columns (TDR §4 table: projects).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions, and Enum
   from sqlalchemy (or db.Enum).
2. class Project(db.Model) with __tablename__ = "projects".
3. Columns exactly per TDR §4: id (UUID PK); group_id (String(36) FK ->
   groups.id, not null, indexed, ondelete="CASCADE"); title
   (String(150), not null); slug (String(170), not null — unique
   together with group_id via a UniqueConstraint("group_id", "slug"));
   description (Text, nullable); gallery_images (JSON, not null,
   default list); tech_tags (JSON, not null, default list); github_url /
   live_url (String(255), nullable each); status (Enum: "planned",
   "in_progress", "completed", "archived"; not null, default
   "completed"); featured (Boolean, not null, default False); created_at
   (DateTime, not null, default now).
4. __table_args__ = (db.UniqueConstraint("group_id", "slug",
   name="uq_project_group_slug"),).
5. __repr__ returning "<Project {self.title}>".

DEBUGGING:
# print(f"[DEBUG] Project full model registered: {Project.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Project.status defaults to "completed" when not set.
- Two Projects with the same slug under different group_id values are
  both allowed (uniqueness is scoped per-group, not global).
- Two Projects with the same slug under the SAME group_id raise an
  IntegrityError.
"""
EOF

cat << 'EOF' > app/models/blog_post.py
"""
FILE PURPOSE: BlogPost model — full columns (TDR §4 table: blog_posts),
per-group per the resolved PDR §12 / TDR §4 decision (group_id NOT
NULL, never platform-wide).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions.
2. class BlogPost(db.Model) with __tablename__ = "blog_posts".
3. Columns exactly per TDR §4: id (UUID PK); group_id (String(36) FK ->
   groups.id, not null, indexed, ondelete="CASCADE"); title
   (String(200), not null); slug (String(220), not null — unique
   together with group_id via UniqueConstraint); content (Text, not
   null); cover_image_path (String(255), nullable); published_at
   (DateTime, nullable — NULL means draft, not yet published, per TDR
   §4); tags (JSON, not null, default list); created_at (DateTime, not
   null, default now).
4. __table_args__ = (db.UniqueConstraint("group_id", "slug",
   name="uq_blogpost_group_slug"),).
5. __repr__ returning "<BlogPost {self.title}>".

DEBUGGING:
# print(f"[DEBUG] BlogPost full model registered: {BlogPost.__tablename__}")

OFFLINE DOCKER TEST CASES:
- A BlogPost with published_at=None is distinguishable as a draft
  (published_at is None) vs. a published post (published_at is a
  datetime).
- `tags` defaults to [] when not set at construction.
- Deleting the parent Group also deletes its BlogPost rows (cascade).
"""
EOF

cat << 'EOF' > app/models/contact_message.py
"""
FILE PURPOSE: ContactMessage model — full columns (TDR §4 table:
contact_messages). group_id is NOT NULL as of v2 — no more nullable
"suggestion" case (PDR §3.2, TDR §4).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions.
2. class ContactMessage(db.Model) with __tablename__ = "contact_messages".
3. Columns exactly per TDR §4: id (UUID PK); group_id (String(36) FK ->
   groups.id, NOT NULL, indexed, ondelete="CASCADE"); name (String(120),
   not null); email (String(255), not null); subject (String(200),
   nullable); message (Text, not null); is_read (Boolean, not null,
   default False); created_at (DateTime, not null, default now,
   indexed — "for inbox sort" per TDR §4).
4. __repr__ returning "<ContactMessage from {self.name}>".

DEBUGGING:
# print(f"[DEBUG] ContactMessage full model registered: {ContactMessage.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Constructing a ContactMessage with group_id=None and attempting to
  persist it raises an IntegrityError (NOT NULL enforcement — this is
  the explicit v2 schema change from TDR §4).
- `is_read` defaults to False on a freshly created row.
- Querying ContactMessage ordered by created_at descending returns the
  most recently created row first (supports the inbox sort use case).
"""
EOF

cat << 'EOF' > app/models/project_request.py
"""
FILE PURPOSE: ProjectRequest model — full columns (TDR §4 table:
project_requests), platform-wide and new in v2 (not tied to a Group at
submission time).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions, and Enum
   from sqlalchemy (or db.Enum).
2. class ProjectRequest(db.Model) with __tablename__ = "project_requests".
3. Columns exactly per TDR §4: id (UUID PK); name (String(120), not
   null); email (String(255), not null); company (String(150),
   nullable); project_type (Enum: "web_app", "mobile_app",
   "desktop_software", "api_backend", "other"; not null); budget_range
   (String(80), nullable); timeline (String(80), nullable); description
   (Text, not null); attachment_path (String(255), nullable); status
   (Enum: "new", "in_review", "contacted", "closed"; not null, default
   "new"); assigned_group_id (String(36) FK -> groups.id, nullable,
   ondelete="SET NULL"); created_at (DateTime, not null, default now,
   indexed — "for inbox sort"); updated_at (DateTime, not null, default
   now, on-update now).
4. assigned_group = db.relationship("Group") (no backref needed — Group
   doesn't need a reverse collection of requests per the PDR's data
   model description in §8).
5. __repr__ returning "<ProjectRequest from {self.name} ({self.status})>".

DEBUGGING:
# print(f"[DEBUG] ProjectRequest full model registered: {ProjectRequest.__tablename__}")

OFFLINE DOCKER TEST CASES:
- ProjectRequest.status defaults to "new" when not set.
- A ProjectRequest can be created with assigned_group_id=None (platform-
  wide submissions don't require a Group at submission time, per PDR
  §8/TDR §4).
- Deleting the assigned Group sets assigned_group_id to NULL on the
  ProjectRequest rather than deleting the request row (ON DELETE SET
  NULL, not CASCADE — distinct from every other FK in this schema).
"""
EOF

cat << 'EOF' > app/models/site_settings.py
"""
FILE PURPOSE: SiteSettings model — full columns (TDR §4 table:
site_settings), singleton row enforced at the application layer
(Integer PK always 1, NOT a UUID like every other model here).

PROMPT FOR LLM IMPLEMENTATION:
1. Import db from app.extensions (no uuid needed — PK is a plain
   Integer, not a UUID string, per TDR §4).
2. class SiteSettings(db.Model) with __tablename__ = "site_settings".
3. Columns exactly per TDR §4: id (Integer PK, default 1); hero_headline
   (String(200), nullable); hero_subheadline (String(300), nullable);
   hero_cta_text (String(80), nullable); hero_images (JSON, not null,
   default list); footer_social_links (JSON, not null, default dict);
   seo_default_title (String(200), nullable); seo_default_description
   (String(300), nullable); seo_default_og_image (String(255),
   nullable); stats_override (JSON, nullable — optional
   {total_groups, total_members, total_projects}; NULL means Home
   computes live counts per TDR §4); updated_at (DateTime, not null,
   default now, on-update now).
4. Add a classmethod get_singleton(cls): returns
   cls.query.get(1) if it exists, else creates, adds, commits, and
   returns a new SiteSettings(id=1) row — so callers never have to
   special-case "does the settings row exist yet" (useful once
   /admin/settings lands in P6, but the helper belongs on the model
   from the start).
5. __repr__ returning "<SiteSettings singleton>".

DEBUGGING:
# print(f"[DEBUG] SiteSettings full model registered: {SiteSettings.__tablename__}")

OFFLINE DOCKER TEST CASES:
- SiteSettings.get_singleton() called on an empty table creates exactly
  one row with id=1 and returns it.
- Calling SiteSettings.get_singleton() a second time returns the SAME
  row (id=1) rather than creating a second one.
- `stats_override` is None by default, and hero_images/footer_social_links
  default to [] / {} respectively.
"""
EOF

git add -A
git commit -q -m "P1 seed: full data model placeholders (Piyush)"
git push -u origin task-piyush-phase1-data-models -f || echo "WARNING: could not push task-piyush-phase1-data-models (check remote access)."

# -------------------------------------------------------------------
# 3c. HARSHLATA — Admin Shell (Frontend)
# -------------------------------------------------------------------
echo ""
echo "--- [Harshlata] Syncing phase1 and creating task-harshlata-phase1-admin-shell ---"
git checkout phase1
git pull origin phase1 || echo "WARNING: could not pull phase1 (offline/new repo — continuing)."
git checkout -B task-harshlata-phase1-admin-shell phase1

mkdir -p app/templates/admin

cat << 'EOF' > app/templates/admin/admin_base.html
<!--
FILE PURPOSE: Fixed-sidebar admin layout — Design Plan §2/§3.2: visually
distinct from the public base.html, "no hero, no parallax, no Owl
Carousel anywhere in /admin/*" (PDR §5.1).

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends nothing %} — this is its OWN base (not base.html), per
   Design Plan §1 principle 4 ("two visually distinct modes"). Standard
   HTML5 doctype, lang="en", responsive viewport meta.
2. Load the same Poppins Google Font as the public site (Style Guide §7
   consistency) plus Bootstrap 4.3.1 css, then the project's own
   static/css/admin.css last.
3. {% block title %}Admin — CodeCrews{% endblock %}.
4. Body layout: a fixed left <nav class="admin-sidebar"> containing the
   "CodeCrews" wordmark and a nav list in this exact order (Design Plan
   §3.2): Dashboard, Groups, Members, Projects, Blog, Messages, Project
   Requests, Settings, Logout. Only Dashboard (url_for('admin.dashboard'))
   and Logout (a POST form calling url_for('auth.logout'), CSRF-token
   included, since logout must never be a bare GET link) are real links
   in P1 — every other item is a disabled/placeholder <span> with a
   code comment noting which milestone wires it up (Groups/Members/
   Projects P3, Blog P5, Messages/Project Requests P4, Settings P6).
5. A top bar with {% block page_title %}{% endblock %} and a
   breadcrumb-style {% block breadcrumb %}{% endblock %}.
6. {% include "partials/flash_messages.html" %} (reused as-is from the
   public partials — Design Plan §1 principle 3: one shared flash
   pattern everywhere).
7. A <main class="admin-content"> wrapping {% block content %}{% endblock %}.
8. Load jQuery + Bootstrap JS + the project's own static/js/admin.js at
   the bottom, then {% block extra_js %}{% endblock %}.

DEBUGGING:
<!-- <script>console.log("[DEBUG] admin_base.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- Rendering any template that extends "admin/admin_base.html" does not
  raise TemplateNotFound/TemplateSyntaxError.
- The rendered HTML contains a <nav class="admin-sidebar"> with all nine
  labels: "Dashboard", "Groups", "Members", "Projects", "Blog",
  "Messages", "Project Requests", "Settings", "Logout".
- No #ftco-loader, #ftco-navbar, or Owl Carousel markup appears anywhere
  in the rendered output (proves the two-mode separation from Design
  Plan §1).
-->
EOF

cat << 'EOF' > app/templates/admin/login.html
<!--
FILE PURPOSE: Admin login screen — Design Plan §4.1: "themed form (same
dark background, Poppins font, amber accent, and loader spinner as the
public site)" even though this page does NOT extend admin_base.html
(it renders before there's a session, so the sidebar shell makes no
sense here).

PROMPT FOR LLM IMPLEMENTATION:
1. Standalone HTML5 page (does not extend admin_base.html OR base.html)
   using the public site's dark background / Poppins font / amber accent
   CSS variables from static/css/style.css, plus {% include
   "partials/loader.html" %} for visual continuity with the public site
   per Design Plan §4.1.
2. A centered card containing the CodeCrews wordmark, a <form
   method="POST"> with {{ form.hidden_tag() }} (CSRF), username field,
   password field, and a submit button styled with the amber primary
   button class.
3. {% include "partials/flash_messages.html" %} above the form, so a
   failed-login inline error "uses the same Bootstrap alert styling as
   the public contact form" (PDR §5.2) — render field-level WTForms
   errors (form.username.errors / form.password.errors) inline too, not
   just the flash.
4. No sidebar, no nav, no footer — this page's only job is the login
   form.

DEBUGGING:
<!-- <script>console.log("[DEBUG] login.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The rendered form contains a hidden csrf_token input.
- Submitting the form with an intentionally wrong password (once
  Utkarsh's auth route is merged) re-renders this same template with a
  visible alert-danger element, not a raw 500.
- The page contains id="ftco-loader" (loader partial reused) but no
  admin-sidebar markup.
-->
EOF

cat << 'EOF' > app/templates/admin/forgot_password.html
<!--
FILE PURPOSE: "Forgot password" request screen — first half of the
signed email-token reset flow (PDR §5.2, resolved per Design Plan §4.1).

PROMPT FOR LLM IMPLEMENTATION:
1. Same standalone dark-themed shell pattern as login.html (loader
   partial, centered card, Poppins/amber styling) — visual consistency
   matters here since this page sits in the same unauthenticated flow.
2. A short explanatory line ("Enter your admin username and we'll email
   a reset link to the registered admin address") above a <form
   method="POST"> with {{ form.hidden_tag() }} and a single username
   field (the target email is ADMIN_NOTIFICATION_EMAIL from config, not
   admin-entered — there's exactly one admin, so no email-lookup step
   is needed, per TDR §16's env reference).
3. {% include "partials/flash_messages.html" %} — on submit, always
   flash the same generic confirmation regardless of whether the
   username matched, to avoid leaking whether an account exists.
4. A link back to /admin/login below the form.

DEBUGGING:
<!-- <script>console.log("[DEBUG] forgot_password.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The rendered form contains a hidden csrf_token input and exactly one
  visible text field (username).
- A link with href pointing at the login route is present.
-->
EOF

cat << 'EOF' > app/templates/admin/reset_password.html
<!--
FILE PURPOSE: "Set new password" screen — second half of the signed
email-token reset flow, reached via the link emailed from
forgot_password.html's submission.

PROMPT FOR LLM IMPLEMENTATION:
1. Same standalone dark-themed shell pattern as login.html/
   forgot_password.html.
2. A <form method="POST"> with {{ form.hidden_tag() }}, a "New Password"
   field, and a "Confirm Password" field (WTForms EqualTo validator
   enforced server-side by Utkarsh's ResetPasswordForm — this template
   just needs to render both fields and their errors).
3. {% include "partials/flash_messages.html" %} for the "token
   expired/invalid" case — the route (auth.py) is responsible for
   redirecting to forgot_password with that flash if the token fails to
   verify; this template only ever renders when the token IS valid.
4. No token value needs to appear as a visible field — it's already
   embedded in the page's own URL (/admin/reset-password/<token>) that
   the form POSTs back to.

DEBUGGING:
<!-- <script>console.log("[DEBUG] reset_password.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The rendered form contains a hidden csrf_token input and two password-
  type inputs (new + confirm).
- Mismatched new/confirm values re-render this same template with a
  visible field-level error rather than silently failing.
-->
EOF

cat << 'EOF' > app/templates/admin/dashboard.html
<!--
FILE PURPOSE: Empty Dashboard — Master Project Blueprint P1 goal is
explicitly "the admin can log in, out, and reset a forgotten password;
no manageable content exists yet." This page exists to prove the
sidebar shell + auth gate work end to end, nothing more.

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "admin/admin_base.html" %}.
2. {% block page_title %}Dashboard{% endblock %}.
3. {% block content %}: a single welcome card ("Welcome back,
   {{ current_user.username }}.") and a placeholder note ("Group,
   Member, Project, Message, and Project Request summary cards land in
   later milestones — see Master Project Blueprint P3/P4.") — NO live
   counts/queries here, since admin.py's dashboard() view intentionally
   passes no extra context in P1.
4. Nothing else — no charts, no tables, no carousels (Design Plan §2:
   admin screens have no marketing chrome).

DEBUGGING:
<!-- <script>console.log("[DEBUG] dashboard.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- Rendering this template with a logged-in current_user does not raise
  a Jinja UndefinedError on current_user.username.
- The rendered output contains the admin-sidebar markup from
  admin_base.html (proves the extends chain works) and no
  <table>/<canvas> elements (proves no premature data wiring).
-->
EOF

git add -A
git commit -q -m "P1 seed: admin shell + auth template placeholders (Harshlata)"
git push -u origin task-harshlata-phase1-admin-shell -f || echo "WARNING: could not push task-harshlata-phase1-admin-shell (check remote access)."

# -------------------------------------------------------------------
# 3d. UTKARSH — Auth & Forms
# -------------------------------------------------------------------
echo ""
echo "--- [Utkarsh] Syncing phase1 and creating task-utkarsh-phase1-auth-forms ---"
git checkout phase1
git pull origin phase1 || echo "WARNING: could not pull phase1 (offline/new repo — continuing)."
git checkout -B task-utkarsh-phase1-auth-forms phase1

mkdir -p app/forms app/routes app/services

cat << 'EOF' > app/forms/auth_forms.py
"""
FILE PURPOSE: Flask-WTF forms for the admin auth flow (PDR §5.2, TDR §5).

PROMPT FOR LLM IMPLEMENTATION:
1. Import FlaskForm from flask_wtf, StringField/PasswordField/
   SubmitField from wtforms, DataRequired/Length/EqualTo from
   wtforms.validators.
2. class LoginForm(FlaskForm): username = StringField("Username",
   validators=[DataRequired()]); password = PasswordField("Password",
   validators=[DataRequired()]); submit = SubmitField("Log In").
3. class ForgotPasswordForm(FlaskForm): username = StringField(
   "Username", validators=[DataRequired()]); submit = SubmitField(
   "Send Reset Link") — matches forgot_password.html's single field
   (target email comes from config, not the form, per TDR §16).
4. class ResetPasswordForm(FlaskForm): password = PasswordField(
   "New Password", validators=[DataRequired(), Length(min=8)]);
   confirm_password = PasswordField("Confirm Password", validators=
   [DataRequired(), EqualTo("password", message="Passwords must
   match.")]); submit = SubmitField("Reset Password").
5. CSRF protection is automatic via FlaskForm + the global CSRFProtect()
   in app/extensions.py — no per-form CSRF code needed (TDR §6).

DEBUGGING:
# print("[DEBUG] auth_forms.py — LoginForm/ForgotPasswordForm/ResetPasswordForm defined")

OFFLINE DOCKER TEST CASES:
- LoginForm(username="", password="x").validate() is False (username
  required).
- ResetPasswordForm(password="longenough1", confirm_password=
  "different").validate() is False (EqualTo mismatch).
- ResetPasswordForm(password="short", confirm_password="short")
  .validate() is False (Length(min=8) rejects it).
"""
EOF

cat << 'EOF' > app/routes/auth.py
"""
FILE PURPOSE: Auth blueprint — login/logout + the signed email-token
password-reset flow (PDR §5.2, resolved per Master Project Blueprint's
P1 map; TDR §5 REST design; TDR §6 session/security rules).

PROMPT FOR LLM IMPLEMENTATION:
1. auth_bp = Blueprint("auth", __name__, url_prefix="/admin").
2. Import login_manager from app.extensions; define
   @login_manager.user_loader def load_user(user_id): return
   AdminUser.query.get(user_id) (import AdminUser from
   app.models.admin_user — only resolves once Piyush's branch is
   merged, note that as a comment).
3. GET/POST "/login" -> login(): instantiate LoginForm(). On valid
   POST, look up AdminUser by username, check_password_hash against the
   submitted password; on success call login_user(admin) (Flask-Login)
   and redirect to url_for("admin.dashboard"); on failure, flash an
   "error"-category message ("Invalid username or password.") and
   re-render "admin/login.html" with the same form (inline error via
   the shared flash pattern, PDR §5.2). If current_user is already
   authenticated, redirect straight to the dashboard instead of
   re-showing the form.
4. POST "/logout" -> logout(): @login_required, call logout_user(),
   flash a "success" message, redirect to url_for("auth.login").
5. GET/POST "/forgot-password" -> forgot_password(): instantiate
   ForgotPasswordForm(). On valid POST, look up AdminUser by the
   submitted username; if found, build a signed token via
   itsdangerous.URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
   .dumps(admin.id, salt="password-reset") and call
   mailer.send_password_reset_email(admin, token) (from
   app.services.mailer — Utkarsh's own file below). Regardless of
   whether the username matched, flash the SAME generic "success"
   message ("If that account exists, a reset link has been sent.") and
   redirect to url_for("auth.login") — never reveal whether the
   username existed (TDR §6 security posture, applied here even though
   there's only one admin).
6. GET/POST "/reset-password/<token>" -> reset_password(token):
   verify the token via the same serializer's .loads(token,
   salt="password-reset", max_age=3600) inside a try/except; on
   failure (BadSignature/SignatureExpired), flash an "error" message
   and redirect to url_for("auth.forgot_password"). On success,
   instantiate ResetPasswordForm(); on valid POST, look up the AdminUser
   by the id embedded in the token, set
   admin.password_hash = generate_password_hash(form.password.data),
   db.session.commit(), flash a "success" message, redirect to
   url_for("auth.login"). On GET (token valid, no POST yet), render
   "admin/reset_password.html" with the form.
7. Rate limiting: apply the shared `limiter` (from app.extensions) to
   the login route specifically, e.g. @limiter.limit("10 per minute"),
   per TDR §6 ("to blunt credential-stuffing attempts against the
   single admin account").

DEBUGGING:
# print(f"[DEBUG] POST /admin/login — attempt for username={request.form.get('username')!r}")
# print(f"[DEBUG] POST /admin/forgot-password — token issued (or silently skipped) for username={request.form.get('username')!r}")

OFFLINE DOCKER TEST CASES:
- POST "/admin/login" with correct seeded credentials redirects (302)
  to "/admin/dashboard" and sets a session cookie.
- POST "/admin/login" with a wrong password returns 200 (re-rendered
  form) and does NOT set an authenticated session.
- GET "/admin/reset-password/not-a-real-token" redirects to
  "/admin/forgot-password" with a flashed error, rather than raising an
  unhandled exception.
- A token generated with max_age=3600 successfully resets the password
  when consumed immediately, and a manually-expired token (mocked
  time) is rejected.
"""
EOF

cat << 'EOF' > app/services/mailer.py
"""
FILE PURPOSE: Flask-Mail wrapper (TDR §8.1). P1 scope is the password-
reset notification ONLY — the Contact/Request-a-Project notification
functions this file will eventually also hold are P4 scope (Master
Project Blueprint §1: "Flask-Mail wrapper for contact/request/
password-reset notifications" — this milestone builds one of the three).

PROMPT FOR LLM IMPLEMENTATION:
1. Import Message from flask_mail, mail from app.extensions,
   current_app, url_for, and Python's logging module
   (logger = logging.getLogger(__name__)).
2. def send_password_reset_email(admin_user, token): build a Message
   with subject "Password Reset Requested" (matches the Notification
   Templates table, PDR §14.2 / TDR appendix), recipients=
   [current_app.config["ADMIN_NOTIFICATION_EMAIL"]], sender=
   current_app.config["MAIL_DEFAULT_SENDER"], and a plain-text body
   containing the signed, time-limited reset link built via
   url_for("auth.reset_password", token=token, _external=True) (PDR
   §14.2: "Signed, time-limited reset link" is the entire content).
3. Call mail.send(msg) inside a try/except; on success log at INFO
   ("Password reset email sent for admin_user=%s", admin_user.username);
   on any exception, log at ERROR with the traceback (logger.exception)
   but do NOT re-raise — per TDR §2/§12, a failed notification email
   must never block or roll back the calling flow (here: the token was
   already generated by auth.py regardless of mail success).
4. Do not add send_contact_notification / send_project_request_notification
   here yet — leave a one-line comment noting they land in P4 alongside
   the Contact/Request-a-Project routes, so this file's shape doesn't
   need to change later, just grow.

DEBUGGING:
# print(f"[DEBUG] mailer.send_password_reset_email — sending to {current_app.config.get('ADMIN_NOTIFICATION_EMAIL')!r}")

OFFLINE DOCKER TEST CASES:
- With MAIL_SUPPRESS_SEND=True (the Docker test config), calling
  send_password_reset_email(admin, "faketoken") does not raise and does
  not attempt any real network I/O.
- The composed Message's subject is exactly "Password Reset Requested"
  and its body contains the token string somewhere within the rendered
  reset URL.
- If mail.send() is monkeypatched to raise, the function still returns
  normally (no unhandled exception propagates to the caller).
"""
EOF

git add -A
git commit -q -m "P1 seed: auth routes, forms & password-reset mailer placeholders (Utkarsh)"
git push -u origin task-utkarsh-phase1-auth-forms -f || echo "WARNING: could not push task-utkarsh-phase1-auth-forms (check remote access)."

# -------------------------------------------------------------------
# 3e. TRIPTI — Docker & Testing Infra
# -------------------------------------------------------------------
echo ""
echo "--- [Tripti] Syncing phase1 and creating task-tripti-phase1-docker-testing ---"
git checkout phase1
git pull origin phase1 || echo "WARNING: could not pull phase1 (offline/new repo — continuing)."
git checkout -B task-tripti-phase1-docker-testing phase1

mkdir -p tests

cat << 'EOF' > tests/conftest.py
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
EOF

cat << 'EOF' > tests/test_admin_auth.py
"""
FILE PURPOSE: P1 acceptance tests — matches the Master Project
Blueprint's P1 Goal verbatim ("the admin can log in, out, and reset a
forgotten password; no manageable content exists yet"). Depends on
Piyush's AdminUser model, Utkarsh's auth routes/forms/mailer, and
Harshlata's templates all being merged into the branch under test.

PROMPT FOR LLM IMPLEMENTATION:
1. test_login_page_loads(client): GET "/admin/login" returns 200 and
   the body contains a csrf_token input.
2. test_login_success_redirects_to_dashboard(client, admin_user,
   admin_password): POST "/admin/login" with the correct
   username/password redirects (302) toward "/admin/dashboard".
3. test_login_failure_shows_inline_error(client, admin_user): POST
   "/admin/login" with a wrong password returns 200 (re-rendered form)
   and the body contains an "alert-danger" (or equivalent error) marker,
   not a raw exception.
4. test_dashboard_requires_login(client): GET "/admin/dashboard"
   without a session redirects (302) to "/admin/login".
5. test_logout_clears_session(logged_in_client): POST "/admin/logout"
   then GET "/admin/dashboard" redirects to "/admin/login" again
   (proves the session was actually cleared, not just the response
   flashed).
6. test_forgot_password_always_flashes_generic_message(client,
   admin_user): POST "/admin/forgot-password" with a username that does
   NOT exist still redirects with the same generic flash as a real
   username would (no user-enumeration leak, per TDR §6).
7. test_reset_password_with_invalid_token_redirects(client): GET
   "/admin/reset-password/garbage-token" redirects to
   "/admin/forgot-password" rather than raising.
8. test_all_models_registered(app): within an app context, assert
   {"admin_users","groups","members","projects","blog_posts",
   "contact_messages","project_requests","site_settings"} is a subset of
   db.metadata.tables.keys() (carried forward from P0's stub-model test,
   now verifying the FULL models load without error).

DEBUGGING:
# print("[DEBUG] running P1 acceptance tests")

OFFLINE DOCKER TEST CASES:
- All eight tests above pass with zero network access (MAIL_SUPPRESS_SEND=True
  suppresses the password-reset email's actual send), entirely against
  the SQLite test database created by conftest.py, once all five task
  branches are integrated into phase1.
"""
EOF

git add -A
git commit -q -m "P1 seed: auth test suite & fixtures placeholders (Tripti)"
git push -u origin task-tripti-phase1-docker-testing -f || echo "WARNING: could not push task-tripti-phase1-docker-testing (check remote access)."

# -----------------------------------------------------------------------
# 4. PHASE COMPLETION ECHO
# -----------------------------------------------------------------------

echo ""
echo "====================================================="
echo "Milestone P1 seeded across 5 task branches off phase1:"
echo "  - task-abhinav-phase1-app-core         (Abhinav)"
echo "  - task-piyush-phase1-data-models       (Piyush)"
echo "  - task-harshlata-phase1-admin-shell    (Harshlata)"
echo "  - task-utkarsh-phase1-auth-forms       (Utkarsh)"
echo "  - task-tripti-phase1-docker-testing    (Tripti)"
echo ""
echo "NEXT STEPS (each developer — developer_workflow_guide.pdf):"
echo "1. Check out your own branch and feed its seeded files to your LLM"
echo "   (code-implementer skill) to generate the real code."
echo "2. Test locally against phase1's shared skeleton."
echo "3. Commit your implementation in logical chunks on top of the seed commit."
echo "4. Push your branch (already pushed once by this script) with your new commits."
echo "5. Open a PR/MR targeting 'phase1' (NEVER MAIN) and notify Abhishek."
echo ""
echo "NEXT STEPS (Abhishek — Team Lead — team_lead_workflow_guide.pdf):"
echo "- Review each of the five PRs; merge approved branches into phase1 in dependency"
echo "  order (Piyush's full models first, then Abhinav's app-core wiring and Utkarsh's"
echo "  auth routes/forms/mailer — both depend on the models existing — then Harshlata's"
echo "  templates, Tripti's test/fixture branch last so the full suite has something"
echo "  complete to run against)."
echo "- Once all five are merged, deploy/test the integrated phase1 branch:"
echo "    docker-compose exec web flask db migrate -m \"P1: full schema\""
echo "    docker-compose exec web flask db upgrade"
echo "    docker-compose -f docker-compose.test.yml run --rm web pytest"
echo "- If testing PASSES: git checkout MAIN && git merge phase1, then tag the release."
echo "- If testing FAILS: git branch -D phase1 (and on remote), recreate phase1 from"
echo "  phase1-seed, and have the relevant developer(s) fix + re-PR their task branch"
echo "  (git fetch --prune; git checkout phase1; git pull; git checkout task-...;"
echo "  git rebase phase1 — per developer_workflow_guide.pdf Scenario B)."
echo "- Once phase1 is merged to MAIN: initialize phase2-seed/phase2 and execute P2.sh."
echo "====================================================="