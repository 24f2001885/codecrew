# PROJECT DEFINITION REPORT: CodeCrews

*(CodeCrews is a placeholder project name carried over from the source planning docs — swap in real branding before build.)*

## 1. Executive Summary

CodeCrews is a public directory platform for coding teams — a "Product Hunt for dev teams." Instead of one person's portfolio, the platform hosts many coding groups, each with its own themed profile page showing their members, tech stack, and project portfolio, all rendered from a shared database instead of hand-edited HTML. There is no public sign-up: exactly one super-admin account controls every piece of content — groups, members, projects, blog posts, and site settings — through a private control panel. Visitors browse anonymously and have exactly two ways to convert into a lead: contacting a specific group directly, or submitting a platform-wide "Request a Project" brief when they want custom work built but don't know which group to ask. A platform-wide Members directory lets visitors browse individual contributors across every group and download a member's resume/CV when one is on file. The product's visual identity — full-screen loader, parallax hero, Owl Carousel sliders, AOS scroll reveals, animated counters, Magnific Popup galleries — is inherited wholesale from an existing single-person "Creative Coder" portfolio template and extended to work across many group profiles without losing that identity.

This PDR reflects the **v2, current** state of the product: the original build prompt's client-side "Save/Bookmark" feature and its "Suggest a Group" nomination form have both been removed and are explicitly out of scope (see §3.2); they are superseded by the Members directory and Request-a-Project channel respectively.

## 2. Project Objectives

### Primary Objectives
- Give every coding group a consistent, animated, on-brand profile page without any group needing to touch code or design.
- Let one super-admin manage the entire platform's content — groups, rosters, projects, blog posts, inbound leads — from a single control panel, with no self-service registration surface for anyone else.
- Convert anonymous visitor traffic into qualified leads through two zero-friction channels: a per-group contact form and a platform-wide Request-a-Project form.
- Make individual contributors discoverable platform-wide (not just inside their own group's page) via a searchable Members directory, including resume/CV downloads.
- Preserve the original template's full animation/interaction language (parallax, AOS, Owl Carousel, Magnific Popup, animated counters/progress bars) across every new screen, so the product feels like one continuous design system rather than a template bolted onto a database.

### Secondary Objectives
- Optional per-group blog/dev-log for teams that want to post updates (confirmed in-scope for the initial build; see §3.1 and the resolved open item in §12).
- Dynamic, per-group SEO metadata so individual group pages are independently discoverable/shareable.
- Forward-compatible tag/category data model so filtering can evolve from free-form tags today into a curated taxonomy later without a schema change (see §12).
- Future scalability: swapping SQLite for PostgreSQL in production, and a second admin/staff role, are both explicitly designed for but **not** built in this phase (see §3.2).

## 3. Scope of Work

### In-Scope
- **Public site:** Landing page (hero slider, platform-wide animated stats, Featured Groups carousel, directory grid, secondary "Request a Project" CTA); full Groups directory with live search/tag filtering and pagination; individual Group Detail pages (hero, About, Team, Tech Stack, dynamic Projects grid with gallery popups, optional per-group Blog section, group-level stats strip, Contact form); a platform-wide Members directory (`/members`) with live search/filtering by name, group, and skill tag, resume download, and a profile popup listing credited projects; a platform-wide Request-a-Project form (`/request-project`) with file attachment support.
- **Lead capture:** Per-group Contact form (`/group/<slug>/contact`) persisted as `ContactMessage` rows and emailed to the admin; platform-wide Request-a-Project form persisted as `ProjectRequest` rows, emailed to the admin, with an admin-side status workflow (New/In Review/Contacted/Closed) and optional assignment to an existing Group.
- **Admin control panel:** Single super-admin login (no self-registration anywhere); full CRUD for Groups, Members (including resume PDF upload), Projects, and Blog posts; Messages inbox (inquiries only); Project Requests inbox with status + assignment; Site Settings screen (hero content, footer/social links, SEO defaults, platform-wide stat overrides); confirm-before-delete modals; CSRF-protected forms throughout.
- **Platform mechanics:** File upload handling (images + PDFs) with type/size validation; responsive Bootstrap 4 layout at all breakpoints; themed 404/500 pages; environment-based config via `.env`; Dockerized dev/test workflow with offline (network-free) automated tests; pagination on all list/directory views; accessibility basics (alt text, aria-labels on icon-only controls) per WCAG 2.1 AA.

### Out-of-Scope
- **Visitor accounts / self-service registration** — there is no sign-up anywhere on the platform, for visitors or for groups; all content enters the system through the single admin.
- **Saved / Bookmarks** — the original v1 spec's client-side, `localStorage`-based bookmarking feature (bookmark icons, "Saved (n)" navbar badge, `/saved` page, `/api/bookmarks`) was fully removed in v2 and is explicitly not part of this build.
- **"Suggest a Group"** — the original v1 form for a visitor to nominate an existing group for the admin to add was removed in v2 and replaced conceptually (not literally) by Request-a-Project, which serves a different purpose (asking for new custom work, not nominating an existing team).
- **Payments / marketplace transactions** — nothing in the source material implies buying/selling; no payment gateway is included.
- **Multiple admin/staff roles** — exactly one admin role exists in this phase; a secondary "staff" tier is a possible future phase, not built now.
- **Native mobile apps** — web-responsive only.
- **Real-time features** (chat, live notifications, websockets) — all interactions are standard request/response.
- **Multi-language / i18n** — not implied anywhere in the source material; single-language (English) build assumed.

## 4. User Personas

### Anonymous Visitor / Prospective Client
Arrives with either general curiosity ("what dev teams exist here, who does what") or a specific need ("I want to hire a team, or get custom software built"). Browses the Groups directory or Members directory, uses live search/filtering to narrow results, opens a Group Detail page or a member's profile popup, and converts either by contacting a specific group or by submitting a platform-wide project request. Never creates an account and has no persistent state between visits — every session starts fresh at discovery.

### Group Member (Represented Profile)
Not a system user in the technical sense — has no login — but is a real stakeholder whose data (photo, bio, role, tech skills, social links, resume) is displayed publicly on both their group's page and the platform-wide Members directory. Their "need" is accurate, current representation and discoverability (e.g., a recruiter finding them via the Members directory and downloading their resume). All of their data is entered and maintained by the super-admin on their behalf.

### Super-Admin
The single operator of the entire platform. Logs into the private control panel to create and maintain every Group, Member, Project, and Blog post; reviews and actions incoming Contact messages and Project Requests (marking read, changing status, assigning a request to a group, deleting spam); and maintains platform-wide settings (hero content, SEO defaults, social links, stat overrides). This is the only role with any write access anywhere in the system.

## 5. Functional Requirements

### 5.1 Admin Control Panel (Foundational — Priority #1)
A sidebar-navigation control panel (Dashboard, Groups, Members, Projects, Blog, Messages, Project Requests, Settings, Logout), visually distinct from the public marketing site (no hero, no parallax, no carousels — a denser utility shell). Every list screen (Groups, Members, Projects, Blog, Messages, Project Requests) supports pagination. Every create/edit form is CSRF-protected and server-side validated, with inline error messages. Every destructive action (delete) requires a confirm modal. Bootstrap flash alerts (auto-dismissing, styled to the theme) report success/error on every submission.

### 5.2 Authentication & Role Access
Exactly one `AdminUser` row ever exists, seeded via a CLI script (`seed.py`) — never through a UI form. Login (`/admin/login`) is a themed form matching the public site's fonts/colors/loader, POSTs credentials validated via Flask-Login, and sets a secure session cookie on success; a failed attempt shows an inline error using the same alert styling as the public contact form. Every `/admin/*` route is gated behind `@login_required`. A password-reset flow (email a signed, time-limited token; admin follows the link to set a new password) is included as the default recovery path — see the resolved decision in §12.

### 5.3 Group Directory & Profiles
The platform's core browsing feature. The Home page shows a hero slider, platform-wide animated stat counters (Total Groups, Total Members, Total Projects), a Featured Groups carousel (groups flagged `featured=True`), and a directory grid teaser. `/groups` is the full browsable directory with live search/tag filtering and pagination. `/group/<slug>` is a themed, one-page-style profile: hero (name/tagline/cover, parallax), About (description, founded date, location, tech tags, member/project counts), Team (member card grid), Tech Stack (animated per-technology proficiency bars), Projects (dynamic grid, each opening a Magnific Popup with full description, tags, screenshot gallery, and GitHub/live-demo links), an optional Blog section, a 4-stat counter strip (Projects Completed, Members, Years Active — computed from `founded_date` — and Total Projects, replacing the removed "Saves Received" slot), and a Contact form scoped to that group.

### 5.4 Members Directory & Resume Management
A platform-wide `/members` route joins every member across every group into a single browsable grid (no group scoping) — the roster view a recruiter or prospective client would want. Each card shows photo, name, role, a clickable badge naming their group, skill tags (if set), social icons, and a "View Resume" icon-button that renders **only** when the member has a `resume_pdf` on file (never a disabled/dead icon). Clicking a card opens a Magnific Popup with full bio, the resume link, and a list of projects the member is credited on. The admin's Member create/edit form includes a Resume/CV (PDF) upload field, restricted by type and size (5MB), stored under a dedicated uploads path. Every icon-only resume button carries an `aria-label` naming the member (e.g., `"Download {member name}'s resume"`).

### 5.5 Lead Capture: Contact & Request-a-Project
Two zero-account lead channels, both server-validated with CSRF tokens and honeypot spam protection:
- **Group Contact** (`/group/<slug>/contact`, POST): name, email, subject, message → persisted as a `ContactMessage` (always tied to a group as of v2) and emailed to the admin. Reviewed in `/admin/messages` (mark read / delete).
- **Request a Project** (`/request-project`, GET form + POST): name, email, company (optional), project type (Web App / Mobile App / Desktop Software / API-Backend / Other), budget range (optional), timeline (optional), required description, optional file attachment (brief/spec doc, PDF or DOCX) → persisted as a `ProjectRequest`, emailed to the admin. Reviewed in `/admin/project-requests`: each row shows requester, project type, submitted date, and an inline-changeable status pill (New / In Review / Contacted / Closed); the admin can optionally assign the request to an existing Group via dropdown.

### 5.6 Search & Live Filtering
A shared filter pattern reused identically across two directories: `/api/groups` (backing `/groups` and the Home directory teaser) and `/api/members` (backing `/members`). Both are keyup-triggered AJAX endpoints — the UI re-renders results with a fade transition and calls `AOS.refresh()` on the newly injected cards so scroll-reveal keeps working on dynamically loaded content. `/api/groups` filters by name and tech tag; `/api/members` filters by name, group, and skill tag.

### 5.7 Blog / Dev-log (per-group)
Resolved as **per-group** (see §12): each `BlogPost` belongs to exactly one Group. Admin CRUD at `/admin/blog`; public rendering as a 3-column card section on that group's detail page. Not platform-wide, and not dropped.

### 5.8 Site Settings & SEO Management
`/admin/settings` lets the admin edit hero slider text/images, footer/social links, default SEO meta (title, description, `og:image`), and an optional manual override for the platform-wide stat counters shown on Home (falls back to live-computed counts when not set). Every Group page additionally generates its own dynamic SEO meta tags (title, description, `og:image`) from that group's own data.

### Ticketing / Support
There is no traditional support-ticket system in this product. The two flows in §5.5 (Contact and Request-a-Project) are the entire visitor→admin communication surface, and both route into admin-side inboxes rather than a customer-facing ticket tracker.

### Password Reset & Notifications
Covered under §5.2 for admin password recovery. Transactional notifications (all via Flask-Mail): "New Contact Message" (to admin, on Contact form submit), "New Project Request" (to admin, on Request-a-Project submit), and "Password Reset Requested" (to admin, on forgot-password submit). See the resolved decision in §12 regarding whether assigning a `ProjectRequest` to a Group also triggers an email.

## 6. Non-Functional Requirements

- **Security:** CSRF tokens on every form (public and admin); passwords hashed with a salted, industry-standard scheme (never plaintext, never reversible); session cookies flagged `HttpOnly`/`Secure` in production; all secrets (SMTP credentials, `SECRET_KEY`, DB URL) loaded from `.env`, never committed to source — this explicitly corrects the legacy template's committed live Gmail credentials, which must be rotated regardless of what's built next.
- **Performance:** Target < 300ms p95 response time for all public read routes and the two `/api/*` filter endpoints under expected traffic (a directory site, not high-throughput transactional system).
- **Uptime:** Target 99.5% availability for the production deployment.
- **Accessibility:** WCAG 2.1 AA as the default standard — alt text on every image (enforced as a required admin field, not optional), `aria-label`s on every icon-only control (burger menu, resume-download icon, popup close button).
- **Responsiveness:** Bootstrap 4 breakpoints (`xs<576`, `sm≥576`, `md≥768`, `lg≥992`, `xl≥1200`) preserved unchanged from the source template; card grids collapse to a single column below `md`; burger menu replaces the top nav below `lg`.
- **Testability:** All automated tests must run fully offline inside Docker containers (no live network calls) — outbound mail is stubbed in the test environment.

## 7. System Architecture (Overview)

A **monolithic Flask application**, organized internally into blueprints (public, api, contact, requests, auth, admin) rather than split into separate services — appropriate given a single admin operator, moderate anticipated traffic, and a feature set with no independent scaling needs (no component here benefits from being deployed or scaled separately from the others). Server-rendered Jinja2 templates deliver HTML directly; the only client-side JavaScript is progressive enhancement (AJAX search/filter, carousel/animation libraries, form UX) — there is no SPA framework and no separate frontend build step. The application is containerized (Docker + `docker-compose`) for both local development and production, running behind Gunicorn with a reverse proxy in production. SQLite is used in development/testing; PostgreSQL is the production database target, with Flask-Migrate managing schema changes across both.

## 8. Database Schema (Summary)

`Group` is the central entity: a Group has many `Member` rows, many `Project` rows, many `BlogPost` rows, and many `ContactMessage` rows (all via `group_id` foreign keys); a Group can also be the optional target of many `ProjectRequest` rows via `assigned_group_id`. `Member` and `Project` each belong to exactly one `Group`. `ContactMessage` always belongs to exactly one `Group` (as of v2 — the old nullable "suggestion" case no longer exists). `ProjectRequest` is platform-wide and does not require a Group at submission time; it may later be assigned to one by the admin. `AdminUser` and `SiteSettings` are both effectively singleton tables (exactly one row each) supporting authentication and platform-wide configuration respectively. Full column-level definitions (types, constraints, indexes) are specified in the companion Technical Design Report.

## 9. Technology Stack

- **Backend:** Python, Flask (blueprint-organized monolith)
- **Templating:** Jinja2 (`base.html` inheritance, `{% include %}` partials, macros for group/member/project cards)
- **Database / ORM:** SQLAlchemy (SQLite for dev/test, PostgreSQL for production) + Flask-Migrate
- **Auth:** Flask-Login, single seeded super-admin row, Werkzeug password hashing
- **Forms / CSRF:** Flask-WTF (CSRF tokens + server-side validation on every form)
- **Mail:** Flask-Mail (SMTP), stubbed in Docker test environment
- **Frontend:** Bootstrap 4, jQuery, AOS, Owl Carousel, Stellar.js, Magnific Popup, Waypoints + jquery.animateNumber, Scrollax (all carried over unchanged from the original template)
- **File uploads:** Werkzeug `secure_filename`, stored under `static/uploads/` (with a dedicated `resumes/` subpath), type/size-validated
- **DevOps:** Docker + `docker-compose` (web + db services), Gunicorn (production WSGI server), environment-based config via `.env` / `python-dotenv`

## 10. Development Phases & Timeline

*(Milestone tags below are labeled M0–M6 per this report's convention; the companion Master Project Blueprint tracks the identical sequence under its own Git-branch tag convention, P0–P6 — the two are the same seven milestones referenced from two documents, not a different plan.)*

| Milestone | Goal | Key Deliverables |
|---|---|---|
| **M0 — Project Setup & Scaffolding** | A blank but fully-themed shell serves at `/` | Flask app factory, config classes, `.env.example`, Docker/`docker-compose`, empty models registered, base layout + partials wired with original static assets |
| **M1 — Data Models & Admin Auth Shell** | Admin can log in/out; no manageable content yet | Full SQLAlchemy models + first migration, `seed.py` (super-admin), `/admin/login`/`logout`, `admin_base.html` shell, empty Dashboard |
| **M2 — Group Directory (Public, Read-Only)** | Visitor can browse seeded groups end-to-end | `/`, `/groups`, `/group/<slug>` on seed data; hero, stats, directory grid, full group detail sections; AOS/sticky-nav/burger verified |
| **M3 — Admin CRUD for Groups, Members, Projects** | Admin fully manages content; public pages go live | CRUD + CSRF forms for Groups/Members/Projects, upload service (incl. resume PDF validation), confirm-delete modals, public pages read live DB |
| **M4 — Contact, Request-a-Project & Messaging** | Both inbound lead channels fully functional | `/group/<slug>/contact` + Flask-Mail + `/admin/messages`; `/request-project` + `ProjectRequest` model + `/admin/project-requests` with status/assignment |
| **M5 — Members Directory, Search/Filter & Blog** | Every remaining interactive feature is live | `/members` + `/api/members`, resume-download UI, Magnific Popup member profiles; `directory-filter.js` shared search pattern; Blog CRUD + per-group public rendering |
| **M6 — Settings, Polish, Hardening & Deploy** | Production-ready build | `/admin/settings`, dynamic per-group SEO, themed 404/500, accessibility pass, upload limits, rate-limiting/honeypot, finalized `requirements.txt`, Gunicorn/WSGI deployment |

## 11. Admin & Permission Model

Only two effective roles exist: an anonymous **Visitor** (read-only on public routes, write-only on the two lead-capture forms) and the single **Super-Admin** (full read/write on everything else). There is no intermediate role in this phase.

| Permission / Resource | Visitor (Anonymous) | Super-Admin |
|---|---|---|
| View public pages (Home, Groups, Group Detail, Members) | ✅ | ✅ |
| Submit Group Contact form | ✅ (write-only) | — |
| Submit Request-a-Project form | ✅ (write-only) | — |
| View/manage Groups (CRUD) | ❌ | ✅ |
| View/manage Members incl. resume upload (CRUD) | ❌ | ✅ |
| View/manage Projects (CRUD) | ❌ | ✅ |
| View/manage Blog posts (CRUD) | ❌ | ✅ |
| View/action Messages inbox | ❌ | ✅ |
| View/action Project Requests inbox | ❌ | ✅ |
| Edit Site Settings | ❌ | ✅ |
| Log into `/admin/*` | ❌ | ✅ |

## 12. Risk Analysis & Mitigation

| Risk | Mitigation |
|---|---|
| Single admin credential compromise grants total content control (no separation of duties) | Strong salted password hashing, rate-limited login attempts, secrets rotation policy, password-reset via signed time-limited email token rather than a weaker mechanism |
| Public upload fields (project screenshots, member resumes, request attachments) become a malware/abuse vector | Strict file-type whitelist per field (images vs. PDF vs. PDF/DOCX), size caps (e.g., 5MB for resumes), `secure_filename` + randomized storage names, uploads served from a non-executable static path |
| Public forms (Contact, Request-a-Project) attract spam/bot submissions | Honeypot field on both forms, plus server-side rate limiting; no CAPTCHA in this phase but the honeypot pattern is extensible to one later |
| Member resumes contain personal data (PII) that's now publicly downloadable | Uploads are opt-in per member (nullable field, admin-controlled), stored under a dedicated path, and the admin — not the member — controls publish/removal, so a takedown is a single admin action |
| Inconsistent/incorrect group or member data entered by the admin degrades trust in listings | Required-field validation (including alt-text fields) and inline form errors on every admin CRUD form, matching the public contact form's validation pattern |
| Free-form tag data (tech tags, skill tags) fragments into inconsistent variants over time (e.g., "React" vs "ReactJS") | JSON-array tag storage is forward-compatible with a future controlled vocabulary without a schema change; flagged as an open item to formalize post-launch (see below) |
| Outbound mail failures (bad SMTP config, provider outage) silently drop leads | Flask-Mail calls are logged (success/failure) independent of the DB write, so a `ContactMessage`/`ProjectRequest` still persists and is visible in the admin inbox even if the notification email fails |
| Migrating from SQLite (dev) to PostgreSQL (prod) introduces subtle type/constraint mismatches | Flask-Migrate manages both from the same migration history from M1 onward; migration is tested against a Postgres container before go-live rather than assumed compatible |

**Resolved decisions carried forward from earlier drafts' open items** (previously flagged as unconfirmed in the source planning docs — settled here so downstream technical planning isn't left guessing):
- **Blog scope:** per-group (§5.7), not platform-wide, not dropped.
- **Password reset:** standard signed email-token flow (§5.2), not a CLI-only reset.
- **Tag/category taxonomy:** free-form JSON tags now (both group tech tags and member skill tags), explicitly designed to support a curated taxonomy later without a schema change — the exact controlled vocabulary itself remains a genuinely open item for a future content-ops pass, not a technical blocker.
- **Project-request assignment notification:** assigning a `ProjectRequest` to a Group does **not** trigger an automatic email in this phase, because Groups have no login/recipient identity in the data model (only `social_links`, not a monitored inbox) — the admin is expected to follow up manually after assigning. Revisit if/when Groups gain a dedicated contact-email field.

## 13. Success Metrics

### Technical KPIs
- 99.5% uptime in production.
- < 300ms p95 response time on public read routes and both `/api/*` filter endpoints.
- Zero unhandled exceptions on the four core flows (browse Groups, browse Members, submit Contact, submit Request-a-Project) across the Docker test suite.

### Business KPIs
- Number of `ProjectRequest` submissions captured per month (primary lead-gen metric).
- Number of `ContactMessage` submissions captured per month, broken out per group.
- Visitor → lead conversion rate (sessions that end in either form submission).

### User Adoption KPIs
- Time-to-find a relevant group or member via search/filter (target: under a few seconds from landing to a filtered result set).
- Bounce rate on the Home page.
- Resume download rate among members who have one on file.

## 14. Appendices

### 14.1 API Endpoint Summary

**Public**
| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/groups` | Groups directory (search/filter UI, seeded by server-rendered results) |
| GET | `/group/<slug>` | Group detail page |
| GET | `/members` | Members directory |
| GET | `/request-project` | Request-a-Project form page |
| POST | `/request-project` | Submit a project request |
| POST | `/group/<slug>/contact` | Submit a group inquiry |
| GET | `/api/groups` | JSON: live-filtered groups (query params: `q`, `tag`, `page`) |
| GET | `/api/members` | JSON: live-filtered members (query params: `q`, `group`, `skill`, `page`) |

**Admin** (all `@login_required`)
| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/admin/login` | Admin login |
| POST | `/admin/logout` | End session |
| GET | `/admin/dashboard` | Overview cards + recent activity |
| GET/POST | `/admin/groups`, `/admin/groups/new`, `/admin/groups/<id>/edit` | Group CRUD |
| POST | `/admin/groups/<id>/delete` | Delete group |
| GET/POST | `/admin/groups/<id>/members`, `.../new`, `.../<member_id>/edit` | Member CRUD (incl. resume upload) |
| POST | `/admin/groups/<id>/members/<member_id>/delete` | Delete member |
| GET/POST | `/admin/groups/<id>/projects`, `.../new`, `.../<project_id>/edit` | Project CRUD |
| POST | `/admin/groups/<id>/projects/<project_id>/delete` | Delete project |
| GET/POST | `/admin/blog`, `/admin/blog/new`, `/admin/blog/<id>/edit` | Blog CRUD |
| POST | `/admin/blog/<id>/delete` | Delete blog post |
| GET | `/admin/messages` | Contact inbox |
| POST | `/admin/messages/<id>/read`, `/admin/messages/<id>/delete` | Mark read / delete |
| GET | `/admin/project-requests` | Project request inbox |
| POST | `/admin/project-requests/<id>/status`, `/admin/project-requests/<id>/assign`, `/admin/project-requests/<id>/delete` | Update status / assign to group / delete |
| GET/POST | `/admin/settings` | Site settings |

### 14.2 Notification Templates
| Template | Trigger | Content |
|---|---|---|
| New Contact Message | A visitor submits a group's contact form | Group name, submitter name/email, message body, link to `/admin/messages` |
| New Project Request | A visitor submits `/request-project` | Requester name/email, project type, description excerpt, link to `/admin/project-requests` |
| Password Reset Requested | Admin submits the forgot-password form | Signed, time-limited reset link |

### 14.3 Glossary
- **Group** — a coding team with its own public profile page, roster, and project portfolio.
- **Member** — an individual contributor belonging to exactly one Group, optionally with a downloadable resume.
- **Project** — a piece of work credited to a Group, shown on that Group's detail page.
- **c-panel** — the private admin control panel (`/admin/*`), accessible only to the single Super-Admin.
- **Featured** — a boolean flag on Groups/Projects controlling inclusion in the Home page's carousel/highlighted sections.
- **ProjectRequest** — a platform-wide (not group-scoped) inbound lead asking for custom work, optionally assignable to an existing Group after submission.
- **ContactMessage** — a group-scoped inbound inquiry submitted through a specific Group's contact form.
