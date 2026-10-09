**TECHNICAL DESIGN REPORT: CodeCrews**

*Companion document to `project-definition-report.md`. Every section below is precise enough to migrate a database, implement an API, and run a security review directly from this document — ambiguity has been resolved here rather than deferred downstream.*

---

## 1. Introduction & Conventions

- **Language/runtime:** Python 3.12, Flask 3.x.
- **Naming conventions:**
  - Variables/functions: `snake_case` (e.g., `get_group_by_slug`, `resume_pdf`).
  - Classes: `PascalCase` (e.g., `ContactMessage`, `ProjectRequest`).
  - Database tables: plural `snake_case` (e.g., `groups`, `project_requests`).
  - Endpoints: RESTful — resource-based nouns, correct HTTP verbs, plural collection names (e.g., `GET /admin/groups`, `POST /admin/groups/<id>/delete`), consistent with the API design in §5.
- **Linting:** `black` (formatting) + `flake8` (linting) for Python, run in CI and locally via `pre-commit`; no equivalent JS bundler/linter is introduced since the frontend is vanilla JS/jQuery, not a bundled framework (see §7).
- **Templates:** Jinja2, `snake_case` template filenames matching their route's purpose (`group_detail.html`, `members_directory.html`).

## 2. System Architecture

**Client-server model:** a single Flask monolith, internally organized into blueprints (`public`, `api`, `contact`, `requests`, `auth`, `admin`) registered by an app factory (`create_app()` in `app/__init__.py`). No microservices split — justified in the PDR (§7) by single-admin operation and no independent scaling needs between components.

**Container orchestration:** `docker-compose.yml` defines two services in dev/test:
- `web` — Flask app served by Gunicorn (prod) or the Flask dev server (local dev), built from the repo `Dockerfile`.
- `db` — SQLite via a mounted volume in dev/test; swapped to a PostgreSQL container image before the M6/P6 hardening phase, using the same `DATABASE_URL`-driven config so no application code changes.

**Data flow, end to end:**
1. Browser requests a public route (e.g., `GET /group/acme-devs`) → Flask routes it to the `public` blueprint → the view queries SQLAlchemy models → Jinja2 renders `group_detail.html` → HTML returns to the browser, where jQuery/AOS/Owl Carousel/Stellar.js progressively enhance it.
2. A visitor submits a form (Contact or Request-a-Project) → the `contact`/`requests` blueprint validates via Flask-WTF (CSRF + field validation + honeypot check) → on success, a row is written via SQLAlchemy, `services/mailer.py` sends the admin notification (best-effort — DB write is not rolled back if mail fails, per PDR §12), and a flash message renders on redirect.
3. The admin authenticates (`auth` blueprint) → Flask-Login sets a session cookie → every subsequent `/admin/*` request is gated by `@login_required` → the `admin` blueprint's CRUD views read/write the same SQLAlchemy models the public site reads, so admin edits are reflected on the public site immediately (no caching layer, no build step).
4. Live search (`/api/groups`, `/api/members`) is a separate, stateless JSON path through the `api` blueprint, backed by shared filter logic in `services/search.py` (deep-dived in §3).

## 3. Flagship Feature: Directory Search & Filter Engine

The single most complex piece of business logic in this product is not a form or a CRUD screen — it's the **shared live-filter engine** backing both `/api/groups` and `/api/members`, because the same filtering pattern has to work correctly across two structurally different entities (Groups: filtered by name + tech tag; Members: filtered by name + group + skill tag) while staying visually and behaviorally identical on the frontend (same debounce, same fade-in, same `AOS.refresh()` re-trigger).

**Design:**

1. **Tag storage:** both `groups.tech_tags` and `members.skill_tags` are stored as native JSON array columns (`["python", "flask", "react"]`) rather than a normalized many-to-many join table. This is a deliberate simplicity trade-off for v1: the PDR's tag taxonomy is explicitly free-form (§12), so a join table with a rigid `tags` lookup table would force premature normalization. The JSON-array approach is forward-compatible — a future migration can promote it to a proper `tags`/`taggables` join table without changing the public API shape.

2. **Query construction (`services/search.py`):** a single `build_filtered_query(model, query_str, tag, extra_filters)` helper is shared by both endpoints:
   - Free-text `query_str` matches case-insensitively against the model's primary text fields (`Group.name`/`Group.tagline` for groups; `Member.name`/`Member.role` for members) using `ilike('%term%')` combined with `or_()`.
   - Tag filtering on a JSON array column is done with the database's native JSON containment operator (PostgreSQL: `tech_tags @> '["react"]'`; SQLite dev/test fallback: application-level Python filtering after a bounded query, since SQLite's JSON1 extension support is inconsistent across environments) — the engine picks the strategy based on `db.engine.dialect.name` so both dev and prod behave correctly without code duplication in the route handlers.
   - `Member`-specific: an additional `group` filter joins to `Group.slug` for the "filter by group" case named in the PDR (§5.6).
   - Every query is paginated via SQLAlchemy's `.paginate()`, with `page` and `per_page` (default 12) query params, returning `{items, page, total_pages, total_count}`.

3. **Edge cases handled explicitly:**
   - Empty `query_str` and empty `tag` → returns the full (paginated) unfiltered collection, not an empty result set.
   - A tag that matches zero records → returns `{items: [], total_count: 0}`, not a 404 — the frontend renders an explicit "no results" state rather than treating it as an error.
   - Tag values are matched case-insensitively by lower-casing both the stored array and the incoming query param at query time, so `"React"` and `"react"` are treated as the same filter (mitigating, without fully solving, the tag-fragmentation risk flagged in PDR §12).
   - Pagination requests beyond the last page return an empty `items` array with a valid `total_pages`, not an error, so the frontend can clamp gracefully.

4. **Why this is the flagship, not the lead-capture forms:** the Contact and Request-a-Project flows (§5 in the PDR) are straightforward validate-then-persist-then-email operations with no algorithmic depth. The search engine is the one piece of logic that has to generalize correctly across two entities, two database dialects, and a shared frontend contract — getting the abstraction boundary right here (one `search.py` service, not two near-duplicate implementations) is what keeps `/groups` and `/members` from drifting apart as the product evolves.

## 4. Database Design

- **`admin_users`**
  - `id` (UUID, Primary Key)
  - `username` (String(80), Unique, Not Null)
  - `password_hash` (String(255), Not Null)
  - `created_at` (DateTime, Not Null, default now)

- **`groups`**
  - `id` (UUID, Primary Key)
  - `name` (String(120), Not Null)
  - `slug` (String(140), Unique, Not Null, Indexed)
  - `tagline` (String(200), Nullable)
  - `description` (Text, Nullable)
  - `logo_path` (String(255), Nullable)
  - `cover_image_path` (String(255), Nullable)
  - `founded_date` (Date, Nullable)
  - `location` (String(120), Nullable)
  - `tech_tags` (JSON, Not Null, default `[]`)
  - `social_links` (JSON, Not Null, default `{}`)
  - `featured` (Boolean, Not Null, default `false`)
  - `created_at` (DateTime, Not Null, default now)
  - `updated_at` (DateTime, Not Null, default now, on update now)

- **`members`**
  - `id` (UUID, Primary Key)
  - `group_id` (UUID, Foreign Key → `groups.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `name` (String(120), Not Null)
  - `role` (String(120), Nullable)
  - `photo_path` (String(255), Nullable)
  - `bio` (Text, Nullable)
  - `skill_tags` (JSON, Not Null, default `[]`)
  - `github_url` (String(255), Nullable)
  - `linkedin_url` (String(255), Nullable)
  - `twitter_url` (String(255), Nullable)
  - `resume_pdf` (String(255), Nullable) — *added in v2*
  - `display_order` (Integer, Not Null, default `0`)
  - `created_at` (DateTime, Not Null, default now)

- **`projects`**
  - `id` (UUID, Primary Key)
  - `group_id` (UUID, Foreign Key → `groups.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `title` (String(150), Not Null)
  - `slug` (String(170), Not Null, Unique together with `group_id`)
  - `description` (Text, Nullable)
  - `gallery_images` (JSON, Not Null, default `[]` — list of image paths)
  - `tech_tags` (JSON, Not Null, default `[]`)
  - `github_url` (String(255), Nullable)
  - `live_url` (String(255), Nullable)
  - `status` (Enum: `planned`, `in_progress`, `completed`, `archived`; Not Null, default `completed`)
  - `featured` (Boolean, Not Null, default `false`)
  - `created_at` (DateTime, Not Null, default now)

- **`blog_posts`** *(per-group, per resolved PDR §12 decision)*
  - `id` (UUID, Primary Key)
  - `group_id` (UUID, Foreign Key → `groups.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `title` (String(200), Not Null)
  - `slug` (String(220), Not Null, Unique together with `group_id`)
  - `content` (Text, Not Null)
  - `cover_image_path` (String(255), Nullable)
  - `published_at` (DateTime, Nullable — `NULL` = draft, not yet published)
  - `tags` (JSON, Not Null, default `[]`)
  - `created_at` (DateTime, Not Null, default now)

- **`contact_messages`**
  - `id` (UUID, Primary Key)
  - `group_id` (UUID, Foreign Key → `groups.id`, **Not Null** — v2 change, no more nullable "suggestion" case)
  - `name` (String(120), Not Null)
  - `email` (String(255), Not Null)
  - `subject` (String(200), Nullable)
  - `message` (Text, Not Null)
  - `is_read` (Boolean, Not Null, default `false`)
  - `created_at` (DateTime, Not Null, default now, Indexed for inbox sort)

- **`project_requests`** *(new in v2)*
  - `id` (UUID, Primary Key)
  - `name` (String(120), Not Null)
  - `email` (String(255), Not Null)
  - `company` (String(150), Nullable)
  - `project_type` (Enum: `web_app`, `mobile_app`, `desktop_software`, `api_backend`, `other`; Not Null)
  - `budget_range` (String(80), Nullable)
  - `timeline` (String(80), Nullable)
  - `description` (Text, Not Null)
  - `attachment_path` (String(255), Nullable)
  - `status` (Enum: `new`, `in_review`, `contacted`, `closed`; Not Null, default `new`)
  - `assigned_group_id` (UUID, Foreign Key → `groups.id`, Nullable, `ON DELETE SET NULL`)
  - `created_at` (DateTime, Not Null, default now, Indexed for inbox sort)
  - `updated_at` (DateTime, Not Null, default now, on update now)

- **`site_settings`** *(singleton — exactly one row, enforced at the application layer)*
  - `id` (Integer, Primary Key, always `1`)
  - `hero_headline` (String(200), Nullable)
  - `hero_subheadline` (String(300), Nullable)
  - `hero_cta_text` (String(80), Nullable)
  - `hero_images` (JSON, Not Null, default `[]`)
  - `footer_social_links` (JSON, Not Null, default `{}`)
  - `seo_default_title` (String(200), Nullable)
  - `seo_default_description` (String(300), Nullable)
  - `seo_default_og_image` (String(255), Nullable)
  - `stats_override` (JSON, Nullable — optional `{total_groups, total_members, total_projects}`; when `NULL`, Home computes live counts)
  - `updated_at` (DateTime, Not Null, default now, on update now)

## 5. REST API Design

### Public
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/` | — | Rendered HTML (hero, stats, featured carousel, directory teaser) |
| GET | `/groups` | Query: `q`, `tag`, `page` | Rendered HTML (server-rendered initial page; live filtering hits `/api/groups` after) |
| GET | `/group/<slug>` | — | Rendered HTML (404 if slug doesn't resolve) |
| GET | `/members` | Query: `q`, `group`, `skill`, `page` | Rendered HTML |
| GET | `/request-project` | — | Rendered HTML (empty form) |
| POST | `/request-project` | Form: `name, email, company?, project_type, budget_range?, timeline?, description, attachment?, csrf_token, honeypot` | 302 redirect + flash on success; re-rendered form with inline errors on validation failure |
| POST | `/group/<slug>/contact` | Form: `name, email, subject?, message, csrf_token, honeypot` | 302 redirect + flash on success; re-rendered form with inline errors on failure |
| GET | `/api/groups` | Query: `q`, `tag`, `page` | `{items: [GroupCard...], page, total_pages, total_count}` |
| GET | `/api/members` | Query: `q`, `group`, `skill`, `page` | `{items: [MemberCard...], page, total_pages, total_count}` |

### Admin (all require an authenticated session; unauthenticated requests redirect to `/admin/login`)
| Method | Path | Request | Response |
|---|---|---|---|
| GET/POST | `/admin/login` | Form: `username, password, csrf_token` | 302 to `/admin/dashboard` on success; inline error on failure |
| POST | `/admin/logout` | — | 302 to `/admin/login` |
| GET | `/admin/dashboard` | — | Rendered HTML: summary cards (group/member/project/message/request counts), recent messages, recent requests |
| GET | `/admin/groups` | Query: `page` | Rendered HTML list |
| GET/POST | `/admin/groups/new` | Form: full Group fields + `logo`, `cover_image` uploads | Create → redirect to list; validation errors re-render form |
| GET/POST | `/admin/groups/<id>/edit` | Same as above, pre-filled | Update → redirect to list |
| POST | `/admin/groups/<id>/delete` | `csrf_token` | Cascades to members/projects/blog/messages per FK `ON DELETE CASCADE`; redirect to list |
| GET | `/admin/groups/<id>/members` | — | Rendered HTML list scoped to the group |
| GET/POST | `/admin/groups/<id>/members/new`, `.../<member_id>/edit` | Form: Member fields + `photo`, `resume_pdf` uploads | Create/update; resume upload validated `.pdf`-only, ≤5MB |
| POST | `/admin/groups/<id>/members/<member_id>/delete` | `csrf_token` | Redirect to member list |
| GET | `/admin/groups/<id>/projects` | — | Rendered HTML list scoped to the group |
| GET/POST | `/admin/groups/<id>/projects/new`, `.../<project_id>/edit` | Form: Project fields + gallery image uploads | Create/update |
| POST | `/admin/groups/<id>/projects/<project_id>/delete` | `csrf_token` | Redirect to project list |
| GET | `/admin/blog` | Query: `group_id?` | Rendered HTML list |
| GET/POST | `/admin/blog/new`, `/admin/blog/<id>/edit` | Form: BlogPost fields (incl. required `group_id`) + cover image | Create/update |
| POST | `/admin/blog/<id>/delete` | `csrf_token` | Redirect to blog list |
| GET | `/admin/messages` | Query: `page`, `is_read?` | Rendered HTML inbox |
| POST | `/admin/messages/<id>/read` | `csrf_token` | Toggle `is_read`; redirect/refresh |
| POST | `/admin/messages/<id>/delete` | `csrf_token` | Delete row; redirect |
| GET | `/admin/project-requests` | Query: `page`, `status?` | Rendered HTML inbox |
| POST | `/admin/project-requests/<id>/status` | `status, csrf_token` | Update `status` enum; redirect/refresh |
| POST | `/admin/project-requests/<id>/assign` | `assigned_group_id, csrf_token` | Set/clear `assigned_group_id`; no automatic email (PDR §12) |
| POST | `/admin/project-requests/<id>/delete` | `csrf_token` | Delete row; redirect |
| GET/POST | `/admin/settings` | Form: SiteSettings fields + hero image uploads | Update singleton row; redirect with flash |

## 6. Security Design

- **CSRF:** global `CSRFProtect()` from Flask-WTF, initialized once in `extensions.py`; every form (public and admin) includes `{{ form.csrf_token }}` and every state-changing route requires it, including admin delete actions (issued as POST, never GET, specifically so they're CSRF-token-protected).
- **Password hashing:** Werkzeug `generate_password_hash`/`check_password_hash` using PBKDF2-SHA256 (Werkzeug's current default); plaintext passwords are never logged or stored, and the seeded admin password is set only via `seed.py` reading from an environment variable, never hard-coded.
- **Session/auth:** Flask-Login manages the session; session cookies are configured `HttpOnly=True` always, `Secure=True` in production (via config class, see §9), `SameSite=Lax`. No "remember me" long-lived token in this phase — session expires with the browser session, consistent with a single-operator admin model where convenience is secondary to limiting the exposure window.
- **RBAC:** enforced structurally, not by a permissions table — every view function under the `admin` blueprint is wrapped in `@login_required`, and the blueprint itself is the RBAC boundary (per PDR §11's two-role model, there's no finer-grained permission to encode).
- **Rate limiting / spam protection:** Flask-Limiter applied to the two public POST endpoints (`/group/<slug>/contact`, `/request-project`) and to `/admin/login` (to blunt credential-stuffing attempts against the single admin account); a honeypot form field (hidden, must arrive empty) on both public forms per PDR §5.5.
- **Upload validation:** every upload field has an explicit extension whitelist enforced server-side (images: `.jpg/.jpeg/.png/.webp`; resumes: `.pdf` only; request attachments: `.pdf/.docx`), a `MAX_CONTENT_LENGTH` cap on the Flask app plus a per-field size check, `secure_filename()` plus a randomized prefix to prevent collisions/overwrites, and files are written under `static/uploads/` (never an executable path).
- **Input validation:** all form input passes through Flask-WTF/WTForms validators (`DataRequired`, `Email`, `Length`, `URL` where relevant) before touching the database; no raw `request.form` values are persisted unvalidated.
- **Secrets handling:** `SECRET_KEY`, `DATABASE_URL`, and all mail credentials load from `.env` via `python-dotenv` and are never committed to source. This explicitly remediates the legacy `server.js` template, which had a live Gmail address and plaintext password committed to the repository — that credential must be rotated independent of this rebuild.

## 7. Frontend Technical Design

- **Framework:** none — server-rendered Jinja2 templates with Bootstrap 4 for layout and jQuery for DOM interaction/AJAX. This is a deliberate choice, not a gap: the product's entire value is in fast, SEO-friendly, server-rendered directory pages, and introducing a client-side framework would add a build pipeline for no corresponding benefit.
- **Templating:** `base.html` defines `{% block %}` regions for title/meta/content/scripts; `templates/partials/_macros.html` defines `group_card()`, `member_card()`, and `project_card()` macros so the three card types render identically wherever they appear (Home, `/groups`, `/members`, `/group/<slug>`).
- **State management:** none needed beyond what's already server-rendered. The only client-side "state" is the current filter query params (`q`, `tag`/`skill`, `page`), held in plain JS variables inside `directory-filter.js` and reflected into the URL query string so filtered views are shareable/bookmarkable via the browser's own URL, not an app-level store.
- **Note on the uploaded high-fidelity mockups:** the two design-reference bundles provided alongside this project (`Create_web_page_design.zip`, `High-fidelity_website_development.zip`) are React/Tailwind prototypes used purely for visual/UX reference during planning. They are **not** the production stack — the build target remains Flask + Jinja2 + Bootstrap 4 + jQuery as specified above and throughout the source planning docs. Screen composition and content decisions from those mockups (e.g., which fields appear on which card) are treated as valid UX input; their React component structure is not.

## 8. Third-Party Integration Design

### 8.1 Email / OTP
Flask-Mail via SMTP, credentials from `.env` (see Appendix, §16). Used for: Contact-form admin notifications, Request-a-Project admin notifications, and admin password-reset tokens. In the Docker test environment, `MAIL_SUPPRESS_SEND=True` (or an equivalent console/log backend) stubs all outbound mail so the full test suite runs with zero external network calls, per the project's offline-first testing philosophy (§10).

### 8.2 Payment Gateway
Not applicable. Nothing in the PDR implies any purchase/payment flow; no payment gateway integration is included in this design.

## 9. Infrastructure & DevOps

- **Docker:** `Dockerfile` builds the Flask app image (Python 3.12-slim base); `docker-compose.yml` runs `web` + `db`; a separate `docker-compose.test.yml` overlay (or profile) swaps in the mail-suppressed config and a disposable test database.
- **Local dev environment:** `docker-compose up` serves the app at `localhost:5000` (or configured port) with a bind-mounted `app/` for live reload during development; `flask db upgrade` applies migrations; `python seed.py` creates the super-admin.
- **Config classes:** `app/config.py` defines `DevelopmentConfig`, `TestingConfig`, and `ProductionConfig`, all reading from `.env`/environment variables, differing primarily in `DEBUG`, `SESSION_COOKIE_SECURE`, `SQLALCHEMY_DATABASE_URI`, and `MAIL_SUPPRESS_SEND`.
- **CI/CD (outline):** on push, run `black --check` + `flake8`, then `docker-compose -f docker-compose.test.yml run web pytest`, then a migration dry-run (`flask db upgrade` against a fresh test DB) before allowing merge to `main` — consistent with the "no direct commits to `main`, branch merges only after its own Docker test suite passes" rule from the Master Project Blueprint.

## 10. Testing Strategy

- **Unit tests:** model constraints/defaults (e.g., `ContactMessage.group_id` NOT NULL enforcement, `ProjectRequest.status` enum default), form validation rules (required fields, honeypot rejection, file-type whitelist), and `services/search.py`'s query-building logic in isolation (mocked/lightweight DB fixtures).
- **Integration tests:** Flask test client hitting real routes against a test database — admin auth (`login required` redirects, successful login/logout), full CRUD round-trips for each admin resource, public route rendering (200s, correct template context), `/api/groups` and `/api/members` filter correctness across the SQLite-vs-Postgres branching described in §3.
- **End-to-end flow tests:** multi-step scenarios run entirely inside the Docker test container — e.g., submit `/request-project` → assert a `ProjectRequest` row exists → log in as admin → assert it appears in `/admin/project-requests` → change its status → assert the change persists.
- **Offline-first constraint:** every test suite runs with `MAIL_SUPPRESS_SEND=True` and no outbound network access is required or permitted for a green build, matching the project's Git+Docker workflow rule that a milestone branch only merges after its own Docker test suite passes.

## 11. Business Logic Algorithms

- No background job queue (e.g., Celery) is required at this product's scale — every write in this system is a direct, synchronous request/response operation (form submit → DB write → best-effort email), and there's no scheduled/batch processing implied anywhere in the PDR.
- The one candidate for a periodic job — purging old, already-read `ContactMessage`/closed `ProjectRequest` rows after a retention window — is **optional** and not required for the initial build; if added later, it would run as a simple scheduled script (cron or `flask` CLI command invoked by the host scheduler), not a queue/worker system.
- The search/filter engine in §3 is the one piece of non-trivial "algorithm" in this product; it is a synchronous request-time computation, not a background process.

## 12. Error Handling & Logging

- **Logging:** Python's standard `logging` module, configured once in the app factory; structured, single-line log records (`timestamp level logger_name message`) rather than a custom JSON format, since there's no downstream log-aggregation requirement named in the PDR.
- **Levels:** `INFO` for business events (contact submitted, project request submitted, admin login success); `WARNING` for validation failures and rate-limit hits; `ERROR` (with full traceback) for unhandled exceptions and failed mail sends.
- **User-facing errors:** themed `404.html`/`500.html` templates matching the public site's visual language (loader, fonts, colors) per PDR §6; neither page ever renders a stack trace or internal error detail to the visitor. Form validation errors render inline next to the relevant field using the same Bootstrap alert styling used elsewhere on the site.
- **Admin-facing errors:** the same flash-alert pattern (auto-dismissing, theme-styled) surfaces both success and error states on every admin CRUD action.

## 13. Operational Runbook

```bash
# First-time setup
cp .env.example .env                  # fill in real values
docker-compose build
docker-compose up -d
docker-compose exec web flask db upgrade
docker-compose exec web python seed.py

# Everyday development
docker-compose up                      # serves the app with live reload
docker-compose exec web flask db migrate -m "message"   # after model changes
docker-compose exec web flask db upgrade

# Running tests (offline, inside Docker)
docker-compose -f docker-compose.test.yml run --rm web pytest

# Production
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

## 14. Technical Dependencies & Licenses

| Package | Purpose | License |
|---|---|---|
| Flask | Web framework | BSD-3-Clause |
| SQLAlchemy | ORM | MIT |
| Flask-Migrate | Migrations | MIT |
| Flask-Login | Session auth | MIT |
| Flask-WTF | Forms + CSRF | BSD-3-Clause |
| Flask-Mail | SMTP mail | BSD-3-Clause |
| Flask-Limiter | Rate limiting | MIT |
| Werkzeug | WSGI/password hashing | BSD-3-Clause |
| python-dotenv | `.env` loading | BSD-3-Clause |
| Gunicorn | Production WSGI server | MIT |
| psycopg2-binary | PostgreSQL driver (prod) | LGPL |
| Bootstrap 4 | CSS framework | MIT |
| jQuery | DOM/AJAX | MIT |
| AOS | Scroll-reveal animation | MIT |
| Owl Carousel | Hero/featured sliders | MIT |
| Stellar.js | Parallax backgrounds | MIT |
| Magnific Popup | Lightbox modals | MIT |
| Waypoints + jquery.animateNumber | Count-up stats | MIT |
| Scrollax | Scroll effects (carried over from original template) | MIT |

## 15. Open Issues & Decisions Pending

Most open items from the source planning docs were resolved in the companion PDR (§12) and reflected in this TDR — blog scope, password-reset mechanism, and the project-request assignment-notification question are all settled. One genuine item remains:

- **Final controlled tag vocabulary:** the schema (§4) stores `tech_tags`/`skill_tags` as free-form JSON arrays deliberately, so this is not a technical blocker — but the actual curated list of suggested tags shown in the filter UI (vs. fully free-text entry) is a content/product decision still pending stakeholder input, not an engineering one.

## 16. Appendix — Environment Variable Reference

```bash
# Core
SECRET_KEY=
FLASK_ENV=development            # development | testing | production
DATABASE_URL=sqlite:///dev.db    # or postgresql://user:pass@host:5432/codecrews

# Mail
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=
MAIL_SUPPRESS_SEND=False         # set True in docker-compose.test.yml
ADMIN_NOTIFICATION_EMAIL=

# Uploads
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=5242880       # 5MB

# Session / security
SESSION_COOKIE_SECURE=False      # True in production
WTF_CSRF_SECRET_KEY=

# Seed (used only by seed.py, never read at runtime)
ADMIN_SEED_USERNAME=
ADMIN_SEED_PASSWORD=
```
