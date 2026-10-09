# UI/UX DESIGN PLAN: CodeCrews

> Derived from `project-definition-report.md` (PDR) and `technical-design-report.md` (TDR). This finalizes and supersedes the earlier v1/v2 iteration docs — every open item those docs flagged as "unconfirmed" (blog scope, password reset, project-request assignment notification) is resolved here as a firm decision, traceable back to PDR §12.

---

## 1. Design Principles

1. **Motion continuity** — preserve the original template's animation language (AOS scroll-reveals, Stellar.js parallax hero, Owl Carousel fade transitions, animated counters/progress bars) across every screen, so scaling from one person's portfolio to many group profiles never feels like a bolted-on database in front of an unrelated design.
2. **Card-first browsing** — every collection (Groups, Members, Projects) renders through the same three Jinja macros (`group_card()`, `member_card()`, `project_card()`), so the one repeating layout unit is genuinely shared code, not just a shared look.
3. **Zero-friction lead capture** — the two ways a visitor reaches the admin (a group's Contact form, or the platform-wide Request-a-Project form) require no auth and share one lightweight validation + flash-alert pattern. This is the platform's entire visitor→admin surface, since there are no accounts anywhere.
4. **Two visually distinct modes** — public pages stay dark-themed, animation-heavy, marketing-style (black background, amber/green accents); the admin c-panel is a separate, denser, sidebar-nav utility shell with no marketing chrome, so an admin never mistakes one context for the other.
5. **Mobile-first grid** — Bootstrap 4 breakpoints carried over unchanged from the source template, including the burger nav and single-column card stacking below `md`.

---

## 2. Wireframe Reference

- **Visitor (public pages):** sticky top navbar that gains a `.scrolled` (shrink + solidify) state after 150px of scroll; one-page anchor-scroll sections within a single Group Detail page; 3–4 column card grids for every directory (Groups, Members, Projects); 4-column footer widget block. "Our Members" is a top-level route (`/members`) with its own card grid — not an anchor inside a group's page — and sits in the primary nav alongside Home and Groups.
- **Super-Admin (c-panel):** fixed left sidebar nav (Dashboard, Groups, Members, Projects, Blog, Messages, Project Requests, Settings, Logout); top bar with page title/breadcrumb; table-list + form-page pattern for CRUD (create/edit as a dedicated page, not a modal, since forms here include file uploads); no hero, no parallax, no Owl Carousel anywhere in `/admin/*`.

---

## 3. Information Architecture (Sitemap)

### 3.1 Public / Shared
- Home / Landing (`/`)
- Groups Directory (`/groups`)
- Group Detail (`/group/<slug>`)
- Our Members — platform-wide directory (`/members`)
- Request a Project / Software (`/request-project`)
- 404 / 500 error pages

### 3.2 Admin
- Login (`/admin/login`)
- Dashboard (`/admin/dashboard`)
- Groups CRUD (`/admin/groups`, `/new`, `/<id>/edit`)
- Members CRUD, nested per group (`/admin/groups/<id>/members`, incl. resume-PDF upload)
- Projects CRUD, nested per group (`/admin/groups/<id>/projects`)
- Blog CRUD (`/admin/blog`) — per-group (§4.2 below)
- Messages Inbox (`/admin/messages`) — inquiries only
- Project Requests Inbox (`/admin/project-requests`)
- Settings (`/admin/settings`)

### 3.3 Staff / Employee
**N/A.** The PDR defines exactly one admin role (§11: Visitor + Super-Admin, nothing between them). No secondary staff tier exists in this build — intentionally empty rather than padded with an invented role.

### 3.4 User / Customer
**N/A.** No visitor accounts exist anywhere in this product (PDR §3.2). Anonymous visitors are fully covered under §3.1 above. There is no persistent visitor state of any kind — every visit is a fresh discovery session that ends either in a Group Contact submission, a Request-a-Project submission, or no conversion at all.

---

## 4. Key User Flows

### 4.1 Registration, Login & Password Reset
- **Registration:** None, by design. Exactly one admin account exists, seeded directly via `seed.py` — never through a UI form (PDR §5.2, TDR §4).
- **Login:** Visitor navigates to `/admin/login` → themed form (same dark background, Poppins font, amber accent, and loader spinner as the public site) → POST validated via Flask-Login → session cookie set → redirect to `/admin/dashboard`. A failed attempt shows an inline error using the same Bootstrap alert styling as the public contact form.
- **Password Reset — RESOLVED:** a standard signed, time-limited email-token flow is the confirmed design (admin enters email → token emailed via Flask-Mail → reset form). This was previously flagged as an open assumption; it is now a firm decision (PDR §12, TDR §5) rather than something to confirm before building.

### 4.2 Core Transaction Flow — "Discover → Engage"
Since there's no purchase in this product, its central job is discovery-to-engagement:
1. Visitor lands on Home, sees the hero slider and platform-wide animated stats.
2. Uses the live search/filter on `/groups` (or the Home directory teaser) to narrow by name or tech tag — the identical filter pattern is also available on `/members` (filtering by name, group, or skill tag).
3. Opens a Group Detail page — parallax hero, About, Team, Tech Stack, Projects, optional Blog — or a member's profile popup on `/members`, which can include a resume download.
4. Opens a project's Magnific Popup for full detail, and/or submits that group's Contact form, and/or — if they want custom work rather than an existing group — goes to `/request-project` to submit a platform-wide project request.
5. There is no persistent "saved" state anywhere in this product. Every return visit starts back at discovery (Home, `/groups`, or `/members`).

**Blog scope — RESOLVED:** per-group, not platform-wide, not dropped. Each `BlogPost` belongs to exactly one Group and renders as a 3-column card section on that group's own detail page (PDR §5.7, TDR §4). This was previously an open item; it is now settled.

### 4.3 Contact & Request-a-Project Flow (substitutes for Ticket Handling / Support)
This is the closest equivalent to a support/lead channel, since it's the *only* path from visitor to admin:
1. Visitor submits a Group's Contact form → stored as a `ContactMessage` row (`group_id` always set) and emailed to the admin. Admin reviews it in `/admin/messages`.
2. Visitor submits `/request-project` (name, project type, budget/timeline, description, optional attachment) → stored as a `ProjectRequest` row and emailed to the admin. Admin reviews it in `/admin/project-requests`, sets a status (New / In Review / Contacted / Closed), and can optionally assign it to an existing Group.
3. **Assignment notification — RESOLVED:** assigning a `ProjectRequest` to a Group does **not** trigger an automatic email, because Groups have no monitored inbox in the data model (only public `social_links`). The admin follows up manually after assignment. This was previously an open item; it is now settled (PDR §12, TDR §8.1) and revisited only if Groups later gain a dedicated contact-email field.
4. New Groups only ever enter the system via the admin manually creating a Group record through Groups CRUD — there is no self-serve or suggestion-based path in this product.

---

## 5. Screen Inventory

**Public**
- Home / Landing
- Groups Directory
- Group Detail
- Our Members (platform-wide directory)
- Request a Project / Software (form page)
- 404 Error
- 500 Error

**Admin**
- Login
- Dashboard
- Groups List
- Group Create/Edit Form
- Members List (per group)
- Member Create/Edit Form (incl. Resume/CV PDF upload field)
- Projects List (per group)
- Project Create/Edit Form
- Blog List
- Blog Post Create/Edit Form
- Messages Inbox (inquiries only)
- Project Requests Inbox
- Settings

---

## 6. Status Badge Convention

| State | Color |
|---|---|
| Featured (Group or Project) | Amber `#ffbd39` (theme primary) |
| Published / Active | Green `#a0f669` (theme secondary) |
| Draft / Pending Review (unpublished blog post) | Gold `#ffc107` (Bootstrap warning) |
| Unread Message | Red dot `#dc3545` (Bootstrap danger) |
| Error / Delete-confirm state | Red `#dc3545` |
| Project Request — New | Blue `#17a2b8` (Bootstrap info) |
| Project Request — In Review | Gold `#ffc107` (Bootstrap warning) |
| Project Request — Contacted | Green `#a0f669` (theme secondary) |
| Project Request — Closed | Gray `#6c757d` (Bootstrap secondary) |

No Saved/Not-Saved badge exists in this design — the Bookmarks feature is permanently out of scope (PDR §3.2).

---

## 7. Style Guide Basics

Bootstrap-based system, confirmed by the TDR (§7) rather than defaulted blind:

- **Framework:** Bootstrap 4.3.1, reused as-is per the TDR's frontend design (§7 — no bundler, no SPA framework).
- **Primary:** `#ffbd39` (amber — primary buttons, badges, active/featured states)
- **Secondary:** `#a0f669` (light green — secondary buttons/accents)
- **Loader accent:** `#F96D00` (orange — the `#ftco-loader` spinner's animated stroke)
- **Base background:** `#000000` — the theme is dark throughout the public site.
- **Base body text:** `#999999` (light gray copy on the dark background)
- **Text on light surfaces:** `#212529` (used inside white card surfaces, e.g. the contact form panel)
- **Font family:** Poppins (Google Font, weights 100–900), falling back to Arial/sans-serif.

---

## 8. Accessibility & Responsiveness

- **Target:** WCAG 2.1 AA (PDR §6).
- **Grid:** Bootstrap 4 breakpoints (`xs<576`, `sm≥576`, `md≥768`, `lg≥992`, `xl≥1200`) unchanged from the source template. Card grids collapse from 3–4 columns down to 1 column below `md`; the burger menu replaces the top nav below `lg`.
- **Icon-only controls** (burger toggle, resume-download icon, popup close button) all require `aria-label`s — not present in the original single-person template and must be added as new work. The resume-download icon specifically uses `aria-label="Download {member name}'s resume"` (TDR §5.4-equivalent field, PDR §5.4).
- **Images** (group logos/covers, member photos, project screenshots) require `alt` text populated from admin-entered fields (group name, member name, etc.) — enforced as a required field in the admin upload forms, not left optional (PDR §6).
