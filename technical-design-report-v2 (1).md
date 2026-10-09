**TECHNICAL DESIGN REPORT: CodeCrews — Version 2**

*Companion to `project-definition-report-v2.md`. Precise enough to migrate a database, implement an API, and run a security review straight from this document.*

> **Version 2 change summary.** Adds: (1) a second login type, `CoderUser`, created only by the super-admin; (2) an access-control engine in which a coder can see a `ProjectRequest` only through a revocable `RequestAccessGrant`; (3) a coder portal (`/coder/*`); (4) public "Join as a Coder" applications (`/join/*`) with a domain-alert engine; (5) an append-only `AuditLog`; (6) private (non-static) storage for request attachments and applicant resumes. M0–M6 milestones are unchanged; the work lands in new milestones M7 and M8. **Impact on already-seeded P0/P1 work** is listed in §15 — it is small, but the `AdminUser.get_id()` and `user_loader` changes must be made before M7 merges.

---

## 1. Introduction & Conventions

- **Language/runtime:** Python 3.12, Flask 3.x.
- **Naming conventions:**
  - Variables/functions: `snake_case` (e.g., `get_granted_request_or_404`, `resume_pdf`).
  - Classes: `PascalCase` (e.g., `CoderUser`, `RequestAccessGrant`).
  - Tables: plural `snake_case` (e.g., `coder_users`, `request_access_grants`).
  - Endpoints: RESTful, resource nouns, correct verbs, plural collections (e.g., `POST /admin/coders/<id>/revoke`).
  - Enum values: lower `snake_case` strings (`brief_only`, `brief_and_contact`).
- **Linting:** `black` + `flake8`, run in CI and via `pre-commit`. No JS bundler (vanilla JS/jQuery).
- **Templates:** Jinja2, `snake_case` filenames matching their route's purpose.
- **Time:** all timestamps stored as UTC; displayed in the viewer's browser-agnostic server format (UTC) in this phase.

## 2. System Architecture

**Client-server model:** a single Flask monolith organized into blueprints registered by `create_app()`:

| Blueprint | URL prefix | Audience |
|---|---|---|
| `public` | `/` | Visitors |
| `api` | `/api` | Visitors (filter JSON) |
| `contact`, `requests` | `/group/<slug>/contact`, `/request-project` | Visitors |
| `join` *(new)* | `/join` | Visitors / applicants |
| `auth` | `/admin` (login/logout/reset) | Super-admin |
| `admin` | `/admin` | Super-admin only |
| `coder_auth` *(new)* | `/coder` (login/logout/invite/reset) | Coders |
| `coder` *(new)* | `/coder` | Active coders only |

**Module additions in Version 2** (paths relative to `app/`):
- `models/`: `coder_user.py`, `request_access_grant.py`, `coder_application.py`, `domain_alert.py` (holds `DomainAlert` and `DomainAlertDelivery`), `audit_log.py`.
- `routes/`: `coder_auth.py`, `coder.py`, `join.py`.
- `forms/`: `coder_forms.py` (coder admin form, coder profile form, coder project form, grant form), `join_forms.py`.
- `services/`: `access.py` (the policy engine, §3.1), `alerts.py` (matching + send, §3.3), `audit.py` (`record_audit()`), `tokens.py` (signed tokens), `private_files.py` (private upload/serve).
- `security/decorators.py` *(new package)*: `super_admin_required`, `coder_required`.
- `templates/`: `coder/*`, `emails/*.txt`, extra `admin/*` and `public/*` pages listed in the UI plan.
- `static/uploads/` stays for **public** media only (logos, covers, photos, screenshots, member resumes).
- `instance/private_uploads/` *(outside the static tree)*: `requests/` and `applications/`.

**Container orchestration:** unchanged — `web` (Gunicorn prod / Flask dev server locally) and `db` (SQLite via volume in dev/test; PostgreSQL container before M6/P6) from the same `DATABASE_URL`-driven config.

**Data flow, end to end:**
1. Public requests render server-side Jinja2, progressively enhanced by JS (unchanged).
2. A visitor form (Contact / Request-a-Project / **Join**) passes Flask-WTF (CSRF, validation, honeypot) → row written → best-effort email via `services/mailer.py` (a mail failure never rolls back the row).
3. The super-admin authenticates → every `/admin/*` view is wrapped in `@super_admin_required`.
4. **(New)** The super-admin creates a coder → invite email with a signed token → coder sets a password at `/coder/accept-invite/<token>` → the coder authenticates at `/coder/login` → every `/coder/*` view is wrapped in `@coder_required`.
5. **(New)** Whenever a coder-facing view needs a project request it calls `services/access.py`; it never queries `ProjectRequest` directly.
6. **(New)** Every sensitive state change calls `record_audit()` in the same transaction as the change.
7. Live search (`/api/groups`, `/api/members`) is unchanged and unauthenticated.

## 3. Flagship Features

### 3.1 Flagship A (new): Access-Control & Grant Engine

This is now the hardest correctness problem in the product: it carries the promise that visitor conversations stay with the super-admin and that revocation is instant. The design principle is **deny by default, one doorway**.

**Doorway.** A coder can reach a `ProjectRequest` only through `RequestAccessGrant`. No coder route queries `project_requests` directly; they call these functions in `services/access.py`:

- `active_grants_query(coder_id)` → grants where `revoked_at IS NULL`, `(expires_at IS NULL OR expires_at > utcnow())`, joined to a coder whose `status = 'active'`.
- `granted_requests_for(coder)` → paginated list of `(ProjectRequest, grant)` pairs from the above.
- `get_granted_request_or_404(coder, request_id)` → returns `(request, grant)` or aborts **404** (not 403, so a coder cannot probe which request ids exist).
- `serialize_request_for_coder(request, grant)` → an **allow-list** dictionary builder (below). Templates receive this dict, never the ORM object, so a later template edit cannot accidentally render a confidential column.

**Allow-list per scope.**

| Field | `brief_only` | `brief_and_contact` |
|---|---|---|
| `id`, `created_at` | ✅ | ✅ |
| `project_type`, `domain_tags`, `budget_range`, `timeline`, `description` | ✅ | ✅ |
| Attachment (via authenticated download route only) | ✅ | ✅ |
| `name`, `email`, `company` (requester) | ❌ | ✅ |
| `status`, `assigned_group_id`, `internal_notes`, `updated_at`, any audit data | ❌ | ❌ |

**Revocation semantics (instant).**
1. Flask-Login's `user_loader` re-reads the coder from the database on **every request** and returns `None` (anonymous) if `status != 'active'`. A revoked coder's open session therefore dies on the next click.
2. A grant's validity is evaluated at query time (above), never cached in the session.
3. Revoking a coder runs, in one transaction: set `status='revoked'`, `revoked_at`, `revoked_by_admin_id`; set `revoked_at` on all of that coder's open grants; write audit rows.
4. Reinstating a coder sets `status='active'` and leaves previous grants revoked: a reinstated coder starts with **zero** grants.
5. Expiry is lazy (a time comparison), so no scheduler is needed.

**Write-scope rules for coders** (enforced server-side, never trusting form data):
- `Project`: create/edit only where `project.group_id == coder.member.group_id`. On create, `group_id` is **forced** from the coder, ignoring any posted value. `featured` and `status='archived'` are absent from `CoderProjectForm`; unknown posted fields are discarded. Editing another group's project id returns 404. Deleting is not routed for coders.
- `Member`: a coder may edit only `coder.member`, and only the whitelist: `role`, `bio`, `skill_tags`, `github_url`, `linkedin_url`, `twitter_url`, `photo`, `resume_pdf`. Never `name`, `group_id`, `display_order`.
- Every coder write records `created_by_coder_id` / `last_edited_by_coder_id` where applicable and an `AuditLog` row with the list of changed field names (not full contents of long text).

**Edge cases handled explicitly.**
- Grant to a revoked/invited (not yet active) coder → rejected with a form error.
- Duplicate active grant for the same (request, coder) → blocked by a partial unique index and a friendly error; re-granting after revoke creates a new row (history preserved).
- Request deleted by admin → grants cascade-delete.
- Group deleted → members cascade → coder accounts cascade; audit rows remain (they store ids as plain strings, no FK).
- A coder whose member is deleted is removed with the member (cascade); the audit log keeps the record.

**Why a service, not decorators alone.** Role decorators answer "may this *kind* of user be on this route?"; they cannot answer "may this coder see *this* request?" The row-level question belongs in one tested module so every coder view gets the same answer.

### 3.2 Flagship B: Directory Search & Filter Engine *(unchanged from Version 1)*

The shared live-filter engine backing `/api/groups` and `/api/members`.

1. **Tag storage:** `groups.tech_tags` and `members.skill_tags` are JSON arrays (free-form per PDR §12), not a join table — forward-compatible with a future `tags`/`taggables` promotion.
2. **Query construction (`services/search.py`):** `build_filtered_query(model, query_str, tag, extra_filters)` is shared. Free text uses `ilike('%term%')` with `or_()` over `Group.name/tagline` or `Member.name/role`. Tag filtering uses PostgreSQL JSON containment in production and an application-level filter after a bounded query on SQLite (dialect chosen from `db.engine.dialect.name`). Members add a `group` filter joined on `Group.slug`. Every query paginates via `.paginate()` (`page`, `per_page` default 12) returning `{items, page, total_pages, total_count}`.
3. **Edge cases:** empty query + tag → full paginated list; unmatched tag → `{items: [], total_count: 0}` (not 404); tags compared case-insensitively; pages beyond the last return empty `items` with a valid `total_pages`.
4. **Version 2 note:** members whose coder account is revoked remain listed; nothing in this engine reads coder tables.

### 3.3 Domain Alert Matching & Delivery (new)

Used by `/admin/project-requests/<id>/notify` (`services/alerts.py`).

1. **Normalization.** `normalize(tags)` lower-cases, trims, collapses internal whitespace, drops empties. Request token set = `normalize(request.domain_tags) ∪ {request.project_type}`. Applicant token set = `normalize(application.domain_tags) ∪ normalize(application.project_types)`.
2. **Eligibility.** An application is eligible iff `email_verified_at IS NOT NULL AND alerts_consent = true AND unsubscribed_at IS NULL AND status IN ('pending','approved')` and it has **no delivery** already recorded for this request (join on `domain_alert_deliveries` → `domain_alerts.project_request_id`). Rejected, converted, unverified, and unsubscribed applicants are never alerted.
3. **Match.** Eligible applicants whose token set intersects the request's token set. Done in Python after one bounded query (≤ 5,000 eligible rows); intersection of small sets is O(n) and identical on SQLite and PostgreSQL (JSON overlap operators are not portable).
4. **Preview, then send.** The admin screen shows the match count and applicant names/domains (admin-only), plus an editable **anonymized summary** (max 600 chars, prefilled `"New {project_type label} project — domains: {tags}."`). The description, budget, timeline, and requester fields are never inserted automatically.
5. **Send.** One `DomainAlert` row (summary, snapshot of type and tags, sender, `is_auto`), then one personalized email per recipient sent over a single reused SMTP connection (`mail.connection()`), at most `ALERT_BATCH_SIZE` (default 100) per click. Each attempt writes a `DomainAlertDelivery` (`sent` or `failed` with a short error). "Send next batch" repeats the process; the exclusion rule in step 2 prevents duplicates. No queue/worker is introduced (per §11).
6. **Per-recipient links** (signed with `itsdangerous`, salt per purpose): `/join/interested/<token>` (payload: delivery id) and `/join/unsubscribe/<token>` (payload: application id).
7. **Auto mode.** If `site_settings.auto_send_domain_alerts` is true, `POST /request-project` additionally runs steps 2–5 with the default summary, `is_auto = true`, `sent_by_admin_id = NULL`, capped at one batch; the admin sees any remainder and can send the next batch manually. Default is **off**.
8. **Privacy invariant (tested):** the rendered alert body contains the summary and the two links only — never requester name/email/company, description, budget, or a request URL.

## 4. Database Design

All primary keys UUID stored as `String(36)` unless stated. New or changed objects are marked **(new)** / **(changed)**.

- **`admin_users`** *(changed: behavior only, no column change)*
  - `id` (UUID, Primary Key)
  - `username` (String(80), Unique, Not Null)
  - `password_hash` (String(255), Not Null)
  - `created_at` (DateTime, Not Null, default now)
  - Class attribute `role = "super_admin"`; `get_id()` returns `"admin:<id>"` (see §6).

- **`groups`** *(unchanged)*
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

- **`members`** *(unchanged)*
  - `id` (UUID, Primary Key)
  - `group_id` (UUID, Foreign Key → `groups.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `name` (String(120), Not Null)
  - `role` (String(120), Nullable)
  - `photo_path` (String(255), Nullable) — image `alt` is always rendered from `name`
  - `bio` (Text, Nullable)
  - `skill_tags` (JSON, Not Null, default `[]`)
  - `github_url`, `linkedin_url`, `twitter_url` (String(255), Nullable)
  - `resume_pdf` (String(255), Nullable)
  - `display_order` (Integer, Not Null, default `0`)
  - `created_at` (DateTime, Not Null, default now)

- **`coder_users`** **(new)**
  - `id` (UUID, Primary Key)
  - `member_id` (UUID, Foreign Key → `members.id`, Not Null, **Unique**, `ON DELETE CASCADE`)
  - `username` (String(80), Unique, Not Null)
  - `email` (String(255), Unique, Not Null) — stored lower-case
  - `password_hash` (String(255), Nullable) — `NULL` until the invite is accepted
  - `status` (Enum: `invited`, `active`, `revoked`; Not Null, default `invited`, Indexed)
  - `created_by_admin_id` (UUID, Foreign Key → `admin_users.id`, Not Null)
  - `invite_sent_at` (DateTime, Nullable)
  - `activated_at` (DateTime, Nullable)
  - `last_login_at` (DateTime, Nullable)
  - `revoked_at` (DateTime, Nullable)
  - `revoked_by_admin_id` (UUID, Foreign Key → `admin_users.id`, Nullable)
  - `revoke_reason` (String(300), Nullable)
  - `created_at` (DateTime, Not Null, default now)
  - `updated_at` (DateTime, Not Null, default now, on update now)
  - Class attribute `role = "coder"`; `get_id()` returns `"coder:<id>"`; `is_active` is `status == "active"`; `group` property returns `member.group`.

- **`projects`** *(changed)*
  - `id` (UUID, Primary Key)
  - `group_id` (UUID, Foreign Key → `groups.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `title` (String(150), Not Null)
  - `slug` (String(170), Not Null, Unique together with `group_id`)
  - `description` (Text, Nullable)
  - `gallery_images` (JSON, Not Null, default `[]`) — **clarified:** list of objects `{"path": str, "alt": str}`; `alt` is required so the accessibility rule (PDR §6) is enforced for admin and coder uploads alike
  - `tech_tags` (JSON, Not Null, default `[]`)
  - `github_url`, `live_url` (String(255), Nullable)
  - `status` (Enum: `planned`, `in_progress`, `completed`, `archived`; Not Null, default `completed`)
  - `featured` (Boolean, Not Null, default `false`) — admin-only
  - `created_by_coder_id` (UUID, Foreign Key → `coder_users.id`, Nullable, `ON DELETE SET NULL`) **(new)**
  - `last_edited_by_coder_id` (UUID, Foreign Key → `coder_users.id`, Nullable, `ON DELETE SET NULL`) **(new)**
  - `created_at` (DateTime, Not Null, default now)
  - `updated_at` (DateTime, Not Null, default now, on update now) **(new)**

- **`blog_posts`** *(unchanged; per-group, admin-only)*
  - `id` (UUID, Primary Key)
  - `group_id` (UUID, Foreign Key → `groups.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `title` (String(200), Not Null)
  - `slug` (String(220), Not Null, Unique together with `group_id`)
  - `content` (Text, Not Null)
  - `cover_image_path` (String(255), Nullable)
  - `published_at` (DateTime, Nullable — `NULL` = draft)
  - `tags` (JSON, Not Null, default `[]`)
  - `created_at` (DateTime, Not Null, default now)

- **`contact_messages`** *(unchanged)*
  - `id` (UUID, Primary Key)
  - `group_id` (UUID, Foreign Key → `groups.id`, Not Null)
  - `name` (String(120), Not Null)
  - `email` (String(255), Not Null)
  - `subject` (String(200), Nullable)
  - `message` (Text, Not Null)
  - `is_read` (Boolean, Not Null, default `false`)
  - `created_at` (DateTime, Not Null, default now, Indexed)

- **`project_requests`** *(changed)*
  - `id` (UUID, Primary Key)
  - `name` (String(120), Not Null)
  - `email` (String(255), Not Null)
  - `company` (String(150), Nullable)
  - `project_type` (Enum: `web_app`, `mobile_app`, `desktop_software`, `api_backend`, `other`; Not Null)
  - `budget_range` (String(80), Nullable)
  - `timeline` (String(80), Nullable)
  - `description` (Text, Not Null)
  - `attachment_path` (String(255), Nullable) — **now relative to `PRIVATE_UPLOAD_FOLDER/requests/`**, not the static tree
  - `status` (Enum: `new`, `in_review`, `contacted`, `closed`; Not Null, default `new`)
  - `assigned_group_id` (UUID, Foreign Key → `groups.id`, Nullable, `ON DELETE SET NULL`)
  - `domain_tags` (JSON, Not Null, default `[]`) **(new)** — admin-editable; used for alert matching
  - `internal_notes` (Text, Nullable) **(new)** — super-admin only; never serialized for coders
  - `created_at` (DateTime, Not Null, default now, Indexed)
  - `updated_at` (DateTime, Not Null, default now, on update now)

- **`request_access_grants`** **(new)**
  - `id` (UUID, Primary Key)
  - `project_request_id` (UUID, Foreign Key → `project_requests.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `coder_id` (UUID, Foreign Key → `coder_users.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `scope` (Enum: `brief_only`, `brief_and_contact`; Not Null, default `brief_only`)
  - `expires_at` (DateTime, Nullable)
  - `granted_by_admin_id` (UUID, Foreign Key → `admin_users.id`, Not Null)
  - `granted_at` (DateTime, Not Null, default now)
  - `revoked_at` (DateTime, Nullable)
  - `revoked_by_admin_id` (UUID, Foreign Key → `admin_users.id`, Nullable)
  - `revoke_reason` (String(300), Nullable)
  - Index `uq_active_grant` — **unique** on (`project_request_id`, `coder_id`) `WHERE revoked_at IS NULL` (partial index; `postgresql_where` and `sqlite_where` both set)

- **`coder_applications`** **(new)**
  - `id` (UUID, Primary Key)
  - `name` (String(120), Not Null)
  - `email` (String(255), Unique, Not Null) — stored lower-case; one application per email
  - `project_types` (JSON, Not Null, default `[]`) — subset of the `project_request.project_type` values
  - `domain_tags` (JSON, Not Null, default `[]`)
  - `headline` (String(160), Nullable)
  - `portfolio_url` (String(255), Nullable)
  - `message` (Text, Nullable)
  - `resume_pdf` (String(255), Nullable) — relative to `PRIVATE_UPLOAD_FOLDER/applications/`
  - `alerts_consent` (Boolean, Not Null)
  - `consent_at` (DateTime, Not Null)
  - `email_verified_at` (DateTime, Nullable)
  - `unsubscribed_at` (DateTime, Nullable)
  - `status` (Enum: `pending`, `approved`, `rejected`, `converted`; Not Null, default `pending`, Indexed)
  - `converted_coder_id` (UUID, Foreign Key → `coder_users.id`, Nullable, `ON DELETE SET NULL`)
  - `admin_notes` (Text, Nullable)
  - `created_at` (DateTime, Not Null, default now, Indexed)
  - `updated_at` (DateTime, Not Null, default now, on update now)

- **`domain_alerts`** **(new)**
  - `id` (UUID, Primary Key)
  - `project_request_id` (UUID, Foreign Key → `project_requests.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `summary` (String(600), Not Null)
  - `project_type_snapshot` (String(30), Not Null)
  - `domain_tags_snapshot` (JSON, Not Null, default `[]`)
  - `is_auto` (Boolean, Not Null, default `false`)
  - `sent_by_admin_id` (UUID, Foreign Key → `admin_users.id`, Nullable)
  - `recipient_count` (Integer, Not Null, default `0`)
  - `created_at` (DateTime, Not Null, default now)

- **`domain_alert_deliveries`** **(new)**
  - `id` (UUID, Primary Key)
  - `alert_id` (UUID, Foreign Key → `domain_alerts.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `application_id` (UUID, Foreign Key → `coder_applications.id`, Not Null, Indexed, `ON DELETE CASCADE`)
  - `status` (Enum: `sent`, `failed`; Not Null)
  - `error` (String(255), Nullable)
  - `sent_at` (DateTime, Not Null, default now)
  - `interested_at` (DateTime, Nullable)
  - Unique constraint (`alert_id`, `application_id`)

- **`audit_logs`** **(new, append-only)**
  - `id` (UUID, Primary Key)
  - `actor_type` (Enum: `admin`, `coder`, `public`, `system`; Not Null)
  - `actor_id` (String(36), Nullable) — plain string, **no FK**, so history survives deletions
  - `action` (String(60), Not Null, Indexed) — e.g. `coder.created`, `coder.revoked`, `grant.created`, `grant.revoked`, `application.converted`, `alert.sent`, `project.coder_edited`
  - `target_type` (String(40), Not Null)
  - `target_id` (String(36), Nullable)
  - `summary` (String(300), Not Null)
  - `details` (JSON, Nullable) — e.g. `{"changed_fields": ["description","tech_tags"]}`
  - `ip_address` (String(45), Nullable)
  - `created_at` (DateTime, Not Null, default now, Indexed)

- **`site_settings`** *(changed; singleton, Integer PK always `1`)*
  - `id` (Integer, Primary Key, always `1`)
  - `hero_headline` (String(200), Nullable)
  - `hero_subheadline` (String(300), Nullable)
  - `hero_cta_text` (String(80), Nullable)
  - `hero_images` (JSON, Not Null, default `[]`)
  - `footer_social_links` (JSON, Not Null, default `{}`)
  - `seo_default_title` (String(200), Nullable)
  - `seo_default_description` (String(300), Nullable)
  - `seo_default_og_image` (String(255), Nullable)
  - `stats_override` (JSON, Nullable)
  - `coder_applications_open` (Boolean, Not Null, default `true`) **(new)**
  - `auto_send_domain_alerts` (Boolean, Not Null, default `false`) **(new)**
  - `updated_at` (DateTime, Not Null, default now, on update now)

**Migration plan.** Migration `M7_coder_accounts` creates `coder_users`, `request_access_grants`, `audit_logs`, adds the new columns to `projects` and `project_requests` (with safe defaults, so existing rows migrate untouched), and moves any existing attachment files from `static/uploads/requests/` to `PRIVATE_UPLOAD_FOLDER/requests/` via a one-off CLI (`flask move-request-attachments`). Migration `M8_coder_applications` creates `coder_applications`, `domain_alerts`, `domain_alert_deliveries` and adds the two `site_settings` columns.

## 5. REST API Design

### Public
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/`, `/groups`, `/group/<slug>`, `/members`, `/request-project` | as before | Rendered HTML |
| POST | `/request-project` | Form: `name, email, company?, project_type, budget_range?, timeline?, description, attachment?, csrf_token, honeypot` | 302 + flash; stores attachment privately; may trigger auto alerts if enabled |
| POST | `/group/<slug>/contact` | Form: `name, email, subject?, message, csrf_token, honeypot` | 302 + flash / inline errors |
| GET | `/join` | — | Rendered form; **404-style "applications closed" page** if `coder_applications_open` is false |
| POST | `/join` | Form: `name, email, project_types[] (≥1 of enum), domain_tags (comma-separated), headline?, portfolio_url?, message?, resume_pdf?, alerts_consent (must be checked), csrf_token, honeypot` | 302 to `/join/thanks`; creates/updates `coder_applications` (existing email → update fields, keep status, resend verification if unverified); sends verification email |
| GET | `/join/thanks` | — | Rendered HTML |
| GET | `/join/verify/<token>` | — | Sets `email_verified_at`, notifies admin once, renders "verified" page; invalid/expired → friendly error page |
| GET | `/join/unsubscribe/<token>` | — | Sets `unsubscribed_at` immediately; renders confirmation (safe direction; link prefetch only reduces mail) |
| POST | `/join/unsubscribe/<token>` | — | Same action; supports mail-client one-click (`List-Unsubscribe-Post`) |
| GET | `/join/interested/<token>` | — | Renders a single-button confirm page (prefetch-safe) |
| POST | `/join/interested/<token>` | `csrf_token` | Sets `interested_at` on the delivery; renders thank-you |
| GET | `/api/groups`, `/api/members` | `q, tag/group/skill, page` | `{items, page, total_pages, total_count}` |

### Admin (all `@super_admin_required`; anonymous → 302 `/admin/login`; coder session → 403)
| Method | Path | Request | Response |
|---|---|---|---|
| GET/POST | `/admin/login` | `username, password, csrf_token` | 302 `/admin/dashboard` / inline error |
| POST | `/admin/logout` | `csrf_token` | 302 `/admin/login` |
| GET/POST | `/admin/forgot-password`, `/admin/reset-password/<token>` | forms | as before |
| GET | `/admin/dashboard` | — | Cards: groups, members, projects, messages, requests, **active coders, pending applications, open grants** |
| — | `/admin/groups…`, `/admin/groups/<id>/members…`, `/admin/groups/<id>/projects…`, `/admin/blog…`, `/admin/messages…` | as in Version 1 | as before |
| GET | `/admin/project-requests` | `page, status?` | Inbox |
| GET | `/admin/project-requests/<id>` | — | **Detail**: full request, internal notes, domain tags, grants table (active + history), alert history |
| POST | `/admin/project-requests/<id>/status`, `/assign`, `/delete` | as before | as before |
| POST | `/admin/project-requests/<id>/notes` | `internal_notes, csrf_token` | Saves; flash |
| POST | `/admin/project-requests/<id>/domain-tags` | `domain_tags, csrf_token` | Saves normalized tags; flash |
| POST | `/admin/project-requests/<id>/grants` | `coder_id, scope (brief_only\|brief_and_contact), expires_at?, csrf_token` | Creates grant, emails coder "Opportunity Assigned", audits `grant.created`; error if coder not `active` or duplicate active grant |
| POST | `/admin/project-requests/<id>/grants/<grant_id>/revoke` | `revoke_reason?, csrf_token` | Sets `revoked_at`; audits `grant.revoked` |
| GET | `/admin/project-requests/<id>/attachment` | — | Streams private attachment (`Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`) |
| GET/POST | `/admin/project-requests/<id>/notify` | GET: preview matches. POST: `summary, csrf_token` | GET: match list and counts. POST: sends one batch; redirect with `sent/failed` counts; audits `alert.sent` |
| GET | `/admin/coders` | `page, status?` | Coder list |
| GET/POST | `/admin/coders/new` | `member_id` *(or inline `group_id, member_name`)*, `username, email, csrf_token` | Creates `coder_users` row `status=invited`, sends invite; audits `coder.created`; error if member already has a coder or email/username taken |
| GET/POST | `/admin/coders/<id>/edit` | `username, email` | Updates; changing email re-sends invite if still `invited` |
| POST | `/admin/coders/<id>/revoke` | `revoke_reason?, csrf_token` | Transaction in §3.1; audits `coder.revoked` |
| POST | `/admin/coders/<id>/reinstate` | `csrf_token` | `status` → `active` if a password exists, else `invited`; audits `coder.reinstated` |
| POST | `/admin/coders/<id>/resend-invite` | `csrf_token` | New signed token; audits |
| GET | `/admin/coder-applications` | `page, status?, verified?` | Inbox |
| GET | `/admin/coder-applications/<id>` | — | Detail incl. resume link and delivery history |
| GET | `/admin/coder-applications/<id>/resume` | — | Streams private resume |
| POST | `/admin/coder-applications/<id>/approve`, `/reject` | `csrf_token` | Sets status; audits; **no email sent** |
| POST | `/admin/coder-applications/<id>/convert` | `group_id, member_name?, role?, username, csrf_token` | Creates `Member` in the chosen group, a `coder_users` row (`invited`), sends invite; sets application `status=converted`, `converted_coder_id`; audits `application.converted` |
| POST | `/admin/coder-applications/<id>/delete` | `csrf_token` | Deletes row and private resume file |
| GET | `/admin/audit-log` | `page, action?, actor_type?` | Read-only list (no edit/delete routes exist) |
| GET/POST | `/admin/settings` | Settings fields incl. `coder_applications_open`, `auto_send_domain_alerts` | Update singleton |

### Coder (all `@coder_required`; anonymous → 302 `/coder/login`; admin session → 403)
| Method | Path | Request | Response |
|---|---|---|---|
| GET | `/coder/accept-invite/<token>` | — | Set-password form (valid, unused token only) |
| POST | `/coder/accept-invite/<token>` | `password, confirm_password, csrf_token` | Sets `password_hash`, `status=active`, `activated_at`; 302 `/coder/login` |
| GET/POST | `/coder/login` | `username, password, csrf_token` | 302 `/coder/dashboard`; rate-limited; only `active` accounts can log in |
| POST | `/coder/logout` | `csrf_token` | 302 `/coder/login` |
| GET/POST | `/coder/forgot-password`, `/coder/reset-password/<token>` | forms | Same generic-message flow as admin |
| GET | `/coder/dashboard` | — | Welcome, group, counts: own projects, active grants |
| GET/POST | `/coder/profile` | `role, bio, skill_tags, github_url, linkedin_url, twitter_url, photo?, resume_pdf?` | Updates own Member only; audits `member.coder_edited` |
| GET | `/coder/projects` | `page` | Own group's projects |
| GET/POST | `/coder/projects/new` | Project fields + gallery uploads with required alt per image (**no** `featured`, **no** `group_id`) | Creates in own group; sets `created_by_coder_id`; audits |
| GET/POST | `/coder/projects/<id>/edit` | same | 404 if project not in own group; sets `last_edited_by_coder_id`; audits with changed field names |
| GET | `/coder/opportunities` | `page` | List of actively granted requests (serialized) |
| GET | `/coder/opportunities/<request_id>` | — | Serialized request per scope; **404** if no active grant |
| GET | `/coder/opportunities/<request_id>/attachment` | — | Streams private attachment if actively granted, else 404 |

## 6. Security Design

- **CSRF:** global `CSRFProtect()`; all state-changing routes are POST with a token, including revoke/grant/convert and the `interested` confirmation.
- **Password hashing:** Werkzeug PBKDF2-SHA256 for both user types. Coder passwords are set only by the coder via a token link; no code path lets an admin read or set one. Minimum 10 characters for coders (admin reset form unchanged at 8; raised to 10 in M7 for consistency).
- **Two user classes, one `current_user`:** Flask-Login stores a **namespaced id** (`"admin:<uuid>"`, `"coder:<uuid>"`). The single `user_loader` parses the prefix, loads the right model, and for coders returns `None` unless `status == 'active'`. Logging into one area first calls `logout_user()`, so one browser holds only one identity at a time.
- **Role decorators** (`security/decorators.py`):
  - `super_admin_required`: not authenticated → redirect to `admin.login`; authenticated as non-admin → `abort(403)`.
  - `coder_required`: not authenticated → redirect to `coder_auth.login`; authenticated as non-coder → `abort(403)`.
  - Blueprint-level `before_request` hooks apply the decorator to **every** view in `admin` and `coder` blueprints, so a newly added route cannot be accidentally public. A test enumerates `app.url_map` and fails if any `/admin/*` or `/coder/*` rule (except an explicit allow-list: login, forgot/reset, accept-invite) lacks the guard.
- **RBAC beyond roles:** row-level rules live in `services/access.py` (§3.1). Coders never get an ORM object for a `ProjectRequest`; only the allow-listed dict.
- **Signed tokens** (`itsdangerous.URLSafeTimedSerializer`, `SECRET_KEY`, distinct salts):
  | Purpose | Salt | Max age | Payload |
  |---|---|---|---|
  | Admin reset | `admin-reset` | 3600 s | admin id + hash fingerprint |
  | Coder invite | `coder-invite` | 259200 s (72 h) | coder id |
  | Coder reset | `coder-reset` | 3600 s | coder id + fingerprint of current `password_hash` |
  | Application verify | `app-verify` | 604800 s (7 d) | application id |
  | Unsubscribe | `app-unsub` | none (long-lived) | application id |
  | Interested | `alert-interest` | 2,592,000 s (30 d) | delivery id |
  Reset and invite tokens include a short SHA-256 fingerprint of the current `password_hash` (or empty string), so **using a token once invalidates it**.
- **Sessions:** `HttpOnly`, `SameSite=Lax`, `Secure` in production; no remember-me. Session lifetime 8 h for coders, browser-session for admin.
- **Rate limiting (Flask-Limiter):** `/admin/login` and `/coder/login` 10/min per IP; `/coder/forgot-password`, `/admin/forgot-password` 5/hour; `/join` POST 5/hour per IP; `/request-project` and contact as before; verify/unsubscribe/interested 30/min per IP.
- **Spam:** honeypot on Contact, Request-a-Project, Join. Email verification gates all alerts.
- **Private files:** request attachments and applicant resumes are stored in `PRIVATE_UPLOAD_FOLDER` (outside `static/`), named with a random UUID prefix, and served only by authenticated routes with `Content-Disposition: attachment` and `nosniff`. They are **not** reachable by URL guessing. Public media (logos, covers, photos, screenshots, member resumes) stays in `static/uploads/`.
- **Upload validation:** images `.jpg/.jpeg/.png/.webp`; resumes `.pdf` only; request attachments `.pdf/.docx`; 5 MB cap via `MAX_CONTENT_LENGTH` plus per-field checks; `secure_filename()` + random prefix; PDF magic-byte check (`%PDF-`) on resume uploads, image header check on images.
- **Input validation:** every field via WTForms validators; coder tag fields length-limited (≤ 20 tags, ≤ 30 chars each).
- **Audit:** `record_audit()` is called inside the same DB transaction as the change; `audit_logs` has no update/delete route or ORM `delete` usage (enforced by a test that greps routes and by a PostgreSQL role grant of INSERT/SELECT only in production deployment notes).
- **Alert email privacy:** see §3.3 step 8; unit-tested.
- **Secrets:** all in `.env`, never committed. The legacy `server.js` Gmail credentials must be rotated.

## 7. Frontend Technical Design

- **Framework:** none. Server-rendered Jinja2 + Bootstrap 4 + jQuery.
- **Templating:** `base.html` (public), `admin/admin_base.html`, **`coder/coder_base.html`** (new). The coder shell reuses `admin.css` plus a small `coder.css` accent so coders can tell which area they are in; no hero, parallax, or carousels in either.
- **Macros:** `group_card()`, `member_card()`, `project_card()`; new admin macros for status pills (`coder_status_pill()`, `grant_scope_badge()`).
- **State:** none beyond URL query params for filters. The coder portal has no client state.
- **JS additions:** `admin.js` confirm modals extended to Revoke/Reinstate/Convert actions (modal text states the consequence, e.g., "This will end the coder's access immediately and revoke their open grants."); `join.js` for the tag-chip input on `/join` (progressive enhancement over a plain comma-separated text input).
- **Mockup note:** the uploaded React/Tailwind prototypes remain visual references only; the build target remains Flask + Jinja2 + Bootstrap 4 + jQuery.

## 8. Third-Party Integration Design

### 8.1 Email / OTP
Flask-Mail via SMTP; `.env` credentials. Version 2 templates (plain-text files in `templates/emails/`): `new_contact`, `new_project_request`, `password_reset_admin`, `password_reset_coder`, `coder_invite`, `opportunity_assigned`, `application_verify`, `application_new_admin`, `domain_alert`. The `domain_alert` template adds `List-Unsubscribe` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` headers. In test config `MAIL_SUPPRESS_SEND=True`; tests capture outgoing messages with `mail.record_messages()` to assert contents. Bulk sends reuse one connection (`with mail.connection() as conn:`).

### 8.2 Payment Gateway
Not applicable; no payment flow in the PDR.

## 9. Infrastructure & DevOps

- **Docker:** unchanged images. The compose files add a named volume for `instance/private_uploads` so private files survive container rebuilds, and it is explicitly **excluded** from the Nginx/static serving config in production.
- **Local dev:** `docker-compose up`; `flask db upgrade`; `python seed.py`. A dev-only CLI `flask create-test-coder` is **not** provided (coders are created through the real admin UI to keep one code path).
- **Config classes:** `DevelopmentConfig`, `TestingConfig`, `ProductionConfig` gain `PRIVATE_UPLOAD_FOLDER`, token max-age settings, `ALERT_BATCH_SIZE`, `UNVERIFIED_APPLICATION_TTL_DAYS`.
- **CI/CD:** `black --check` + `flake8` → `docker-compose -f docker-compose.test.yml run web pytest` → migration dry-run on a fresh DB → **authorization matrix job must pass before any M7/M8 branch merges** → merge to `main`.

## 10. Testing Strategy

- **Unit:** token helpers (expiry, tamper, single-use fingerprint); `serialize_request_for_coder` allow-list (asserts forbidden keys are absent per scope); `services/alerts.py` normalization, eligibility, match, dedupe; form validators (alt required, consent required, tag limits).
- **Integration:** CRUD round-trips for coders, grants, applications; `/join` full flow (apply → verify → admin sees it); coder invite flow (create → accept → login); coder project create/edit scoped to own group.
- **Authorization matrix (merge gate for M7):** a parametrized test iterates every route in `app.url_map` × {anonymous, coder, admin, revoked coder} and asserts the expected status from a declarative table (e.g., `/admin/messages`: anonymous 302, coder 403, admin 200, revoked coder 302). Plus targeted leak tests:
  1. Coder cannot GET any `/admin/*` URL; admin session gets 403 on `/coder/*`.
  2. With `brief_only`, the `/coder/opportunities/<id>` HTML contains neither requester email, name, company, nor `internal_notes` text (seeded with unique sentinel strings).
  3. With `brief_and_contact`, requester fields appear; `internal_notes` still does not.
  4. Request with no grant, revoked grant, or expired grant → 404 on detail and attachment routes.
  5. Revoking a coder while their session is open → their next request redirects to login; their grants are all revoked.
  6. Reinstated coder sees zero opportunities.
  7. Coder POSTs another group's `group_id`, `featured=true`, or `member_id` → ignored/404; the stored row is unchanged apart from allowed fields.
  8. Request attachments and applicant resumes are not retrievable under `/static/…`.
  9. Alert email body contains no sentinel requester data; recipients exclude unverified, unsubscribed, rejected, converted, and already-alerted applicants.
  10. `audit_logs` row exists for each sensitive action; no route can modify or delete them.
- **End-to-end flow tests (in Docker):** (a) visitor submits `/request-project` → admin sets domain tags → admin previews alert → sends → applicant clicks *interested* → admin sees it → admin converts the applicant → grants the request (`brief_only`) → coder logs in and sees only the brief → admin revokes → coder gets 404. (b) Existing Version 1 flows regress-tested.
- **Offline-first:** `MAIL_SUPPRESS_SEND=True`, no network calls, disposable SQLite DB.

## 11. Business Logic Algorithms

- No Celery/worker queue. Alert sends are bounded batches (§3.3); invites and verification are single emails.
- **Retention CLI commands** (run from host cron; optional but recommended): `flask purge-unverified-applications` deletes `coder_applications` that are unverified for more than `UNVERIFIED_APPLICATION_TTL_DAYS` (default 30), including private resume files; `flask purge-old-requests` (optional) removes read messages and closed requests past a retention window; audit log is **never** auto-purged in this phase.
- Grant expiry and coder revocation are evaluated lazily at read time; there is no scheduled expiry job.
- Search/filter engine and alert matching are synchronous request-time computations (§3.2, §3.3).

## 12. Error Handling & Logging

- **Logging:** standard `logging`, single-line records `timestamp level logger_name message`.
- **Levels:** `INFO` business events (coder created/activated/revoked, grant created/revoked, application received/verified, alert batch sent); `WARNING` validation failures, rate-limit hits, **authorization denials (403/404 on coder routes, with coder id)**; `ERROR` with traceback for unhandled exceptions and failed mail sends.
- **Never log:** passwords, raw tokens, requester contact details, or applicant resume contents.
- **User-facing errors:** themed `404.html`/`500.html`; new `403.html` for role mismatches; `coder/access_changed.html` when a coder's account or grant is revoked mid-session (shown instead of a bare redirect when the previous page was in `/coder/*`). No stack traces ever render.
- **Admin- and coder-facing errors:** the shared auto-dismissing flash alert pattern.

## 13. Operational Runbook

```bash
# First-time setup
cp .env.example .env                  # fill in real values
docker-compose build
docker-compose up -d
docker-compose exec web flask db upgrade
docker-compose exec web python seed.py

# Everyday development
docker-compose up
docker-compose exec web flask db migrate -m "message"
docker-compose exec web flask db upgrade

# Version 2 one-off (after M7 migration, only if attachments already exist)
docker-compose exec web flask move-request-attachments

# Maintenance (host cron, daily)
docker-compose exec web flask purge-unverified-applications

# Tests (offline)
docker-compose -f docker-compose.test.yml run --rm web pytest
docker-compose -f docker-compose.test.yml run --rm web pytest tests/test_authorization_matrix.py

# Production
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
```

## 14. Technical Dependencies & Licenses

| Package | Purpose | License |
|---|---|---|
| Flask | Web framework | BSD-3-Clause |
| SQLAlchemy | ORM | MIT |
| Flask-Migrate | Migrations | MIT |
| Flask-Login | Session auth (admin + coder) | MIT |
| Flask-WTF | Forms + CSRF | BSD-3-Clause |
| Flask-Mail | SMTP mail | BSD-3-Clause |
| Flask-Limiter | Rate limiting | MIT |
| Werkzeug | WSGI / hashing | BSD-3-Clause |
| itsdangerous | Signed tokens (ships with Flask) | BSD-3-Clause |
| email-validator | Email field validation | CC0-1.0 |
| python-dotenv | `.env` loading | BSD-3-Clause |
| Gunicorn | Production server | MIT |
| psycopg2-binary | PostgreSQL driver | LGPL |
| pytest, pytest-flask | Tests | MIT |
| Bootstrap 4, jQuery, AOS, Owl Carousel, Stellar.js, Magnific Popup, Waypoints + jquery.animateNumber, Scrollax | Frontend | MIT |

No new third-party package is needed for Version 2.

## 15. Open Issues & Decisions Pending

**Impact on already-seeded P0/P1 work (must be applied before M7 merges):**
1. `AdminUser.get_id()` must return `"admin:<id>"` and gain `role = "super_admin"` (P1 model prompt currently relies on `UserMixin`'s default).
2. `auth.py`'s `user_loader` must parse the namespaced id and dispatch to `AdminUser` or `CoderUser`; `admin.dashboard` must switch from `@login_required` to `@super_admin_required` (P1 prompts specify plain `@login_required`).
3. `tests/conftest.py`'s `logged_in_client` keeps working but its expected cookie contents change; add `logged_in_coder_client`, `granted_request`, and sentinel-data fixtures in M7.
4. `static/uploads/requests/` in the P0 skeleton is superseded by the private folder (a no-op for P0, since no requests exist yet).

**Genuine open items:**
- **Final controlled tag vocabulary** (unchanged): schema is free-form; the curated list is a content decision. It now also affects alert-match quality; case-insensitive normalization mitigates but does not solve synonyms (e.g., "react" vs "reactjs").
- **Coder project approval queue (decision D5):** defaulted to *publish immediately* with audit. If you want review-before-publish, add `projects.review_status` and an admin approval list; a small additive change.
- **Coder blog posting and project deletion (D6):** defaulted to admin-only; trivial to extend later.
- **Coder-to-admin in-app messaging:** out of scope; coders reach the admin outside the platform.
- **Granular per-coder permissions:** out of scope; the single coder role plus per-request grants covers the current requirement.

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
UPLOAD_FOLDER=app/static/uploads                 # public media only
PRIVATE_UPLOAD_FOLDER=instance/private_uploads   # request attachments + applicant resumes (never served statically)
MAX_CONTENT_LENGTH=5242880       # 5MB

# Session / security
SESSION_COOKIE_SECURE=False      # True in production
WTF_CSRF_SECRET_KEY=
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
ADMIN_SEED_USERNAME=
ADMIN_SEED_PASSWORD=
```
