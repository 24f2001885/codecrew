#!/usr/bin/env bash
# P2.sh
# CodeCrews — Milestone P2: Group Directory (Public, Read-Only)
#
# Developer: Abhishek (Team Lead and sole developer)
#
# Goal (Master Project Blueprint v2): a visitor can browse seeded groups
# end to end — Home, /groups, /group/<slug> — with the original template's
# animation set intact. No admin write access yet; data comes from sample
# data created by `python seed.py --sample`.
#
# This script contains zero application logic. Every file is a heredoc
# holding a PROMPT for an LLM (code-implementer) to fill in later, all on
# ONE task branch (single developer).
#
# Source docs: master-project-blueprint-v2.md §1 + §3 (P2),
# project-definition-report-v2.md §5.3, technical-design-report-v2.md §4/§5,
# ui-ux-design-plan-v2.md §2/§4.2.

set -e

echo "====================================================="
echo "CodeCrews — P2: Group Directory (Public, Read-Only)"
echo "Developer: Abhishek"
echo "====================================================="

# ---------------------------------------------------------------------
# 1. PHASE INITIALIZATION
# ---------------------------------------------------------------------
echo ""
echo "--- Phase 2 initialization ---"
git checkout MAIN
git pull origin MAIN || echo "WARNING: could not pull MAIN (offline — continuing)."

if git show-ref --quiet refs/heads/phase2-seed; then
    echo "phase2-seed already exists — skipping."
else
    git checkout -b phase2-seed MAIN
fi
if git show-ref --quiet refs/heads/phase2; then
    echo "phase2 already exists — skipping."
else
    git checkout -b phase2 phase2-seed
fi
git push -u origin phase2-seed || echo "WARNING: could not push phase2-seed."
git push -u origin phase2 || echo "WARNING: could not push phase2."

# ---------------------------------------------------------------------
# 2. DIRECTORIES
# ---------------------------------------------------------------------
echo ""
echo "--- Verifying directories on phase2 ---"
git checkout phase2
mkdir -p app/services app/routes app/templates/public app/templates/partials
mkdir -p app/static/css app/static/js app/static/images tests
git add -A
git commit -q -m "P2: skeleton verification" || echo "Nothing to commit."
git push origin phase2 || echo "WARNING: could not push phase2."

# ---------------------------------------------------------------------
# 3. TASK BRANCH
# ---------------------------------------------------------------------
echo ""
echo "--- Creating task-abhishek-phase2-group-directory ---"
git checkout -b task-abhishek-phase2-group-directory phase2

cat << 'EOF' > app/services/sample_data.py
"""
FILE PURPOSE: Sample groups, members and projects so the public pages have
something to show before the admin CRUD exists (P3). Used only by
`python seed.py --sample` and by tests.

PROMPT FOR LLM IMPLEMENTATION:
1. Import db and the Group, Member, Project models.
2. def create_sample_data(): idempotent — if any Group already exists,
   print "Sample data already present — skipping." and return 0.
3. Create 6 groups with distinct names/slugs (e.g. "acme-devs"), tagline,
   description (2 paragraphs), founded_date (spread across 2018-2024),
   location, tech_tags (3-5 lowercase tags each), social_links
   {"github": url, "website": url}, featured=True for exactly 3 of them,
   logo_path and cover_image_path pointing at placeholder files under
   static/images/ (e.g. "images/placeholder-logo.png").
4. For each group create 3-5 members (name, role, bio, skill_tags,
   github_url, linkedin_url, display_order 0..n) with photo_path
   placeholders; leave resume_pdf None for most and set a fake relative
   path for one member in two groups so the resume icon can be tested.
5. For each group create 2-4 projects (title, slug unique within the
   group, description, tech_tags, gallery_images as a list of objects
   {"path": "images/placeholder-shot.png", "alt": "<descriptive text>"},
   github_url, live_url, status mixing completed/in_progress, featured
   True for one project per group).
6. Commit once at the end and return the number of groups created.
7. Write no real personal data — names and URLs are obviously fictional.

DEBUGGING:
# print(f"[DEBUG] create_sample_data created {n} groups, {m} members, {p} projects")

OFFLINE DOCKER TEST CASES:
- On an empty database, create_sample_data() creates 6 groups, exactly 3
  featured, and every Group.slug is unique.
- Calling it a second time creates nothing (counts unchanged).
- Every gallery image object has a non-empty "alt".
"""
EOF

cat << 'EOF' > seed.py
"""
FILE PURPOSE: Database seed CLI — P2 adds an optional --sample flag.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything P1 already does (create the single super-admin from
   ADMIN_SEED_USERNAME / ADMIN_SEED_PASSWORD, idempotent, never print the
   password, exit non-zero when env vars are missing).
2. Add argparse with one optional flag --sample. When passed, after the
   admin step, call app.services.sample_data.create_sample_data() and print
   how many groups were created.
3. Make the admin step skippable when the flag is --sample-only (a second
   optional flag) so tests and demos can add sample data without
   admin env vars.
4. `if __name__ == "__main__": run()`.

DEBUGGING:
# print(f"[DEBUG] seed.py flags: sample={args.sample} sample_only={args.sample_only}")

OFFLINE DOCKER TEST CASES:
- `python seed.py --sample-only` creates sample groups and no admin row.
- `python seed.py` without flags behaves exactly like P1.
- Running with --sample twice does not duplicate groups.
"""
EOF

cat << 'EOF' > app/templates/partials/_macros.html
<!--
FILE PURPOSE: The three shared card macros — group_card(), member_card(),
project_card() — so every directory renders the same markup (Design Plan
§1 principle 2, TDR v2 §7).

PROMPT FOR LLM IMPLEMENTATION:
1. {% macro group_card(group) %}: a Bootstrap column wrapper with
   data-aos="fade-up"; logo/cover <img> with alt="{{ group.name }} logo";
   name linking to url_for('public.group_detail', slug=group.slug);
   tagline; up to 4 tech tag pills; a "Featured" amber badge when
   group.featured; member and project counts.
2. {% macro member_card(member) %}: photo <img alt="{{ member.name }}">,
   name, role, a clickable group badge linking to the group's page,
   skill tag pills (only if present), social icon links, and a
   "View Resume" icon button rendered ONLY when member.resume_pdf is set,
   with aria-label="Download {{ member.name }}'s resume" (PDR §5.4). Add
   data-member-id for the P5 popup.
3. {% macro project_card(project) %}: first gallery image with its own alt
   text, title, status pill, tech tags, and a link with class
   js-project-popup (Magnific Popup wiring lives in main.js).
4. Use only variables passed in; no database access in templates.
5. Escape all user text (Jinja autoescape on; never use |safe).

DEBUGGING:
<!-- <script>console.log("[DEBUG] _macros.html loaded");</script> -->

OFFLINE DOCKER TEST CASES:
- Rendering group_card with a featured group includes the text "Featured".
- member_card with resume_pdf=None contains NO element with the word
  "Resume"; with a path set it contains an aria-label naming the member.
- Every <img> rendered by the three macros has a non-empty alt attribute.
-->
EOF

cat << 'EOF' > app/routes/public.py
"""
FILE PURPOSE: Public blueprint — P2 adds the real Home, /groups and
/group/<slug> pages (PDR §5.3).

PROMPT FOR LLM IMPLEMENTATION:
1. Keep public_bp = Blueprint("public", __name__) and the existing index
   route name `index`.
2. index(): query featured groups (Group.featured is True, newest first,
   max 6), the first 6 groups for the directory teaser, and platform
   stats: total groups, total members, total projects via count queries.
   Render "public/home.html" with featured_groups, teaser_groups, stats.
   (A SiteSettings.stats_override is honored later in P6 — leave a
   comment.)
3. groups(): GET /groups, query params page (default 1, min 1) and
   per_page=12 pagination using Group.query.order_by(Group.name)
   .paginate(). Render "public/groups_directory.html" with the page object.
   (q/tag filtering arrives in P5 — leave a comment.)
4. group_detail(slug): GET /group/<slug>; Group.query.filter_by(slug=slug)
   .first_or_404(). Members ordered by display_order, projects ordered by
   featured desc then created_at desc. Compute years_active from
   founded_date (None-safe, whole years). Render
   "public/group_detail.html" with group, members, projects, stats.
5. No write routes here. No admin imports.

DEBUGGING:
# print(f"[DEBUG] GET /group/{slug} -> members={len(members)} projects={len(projects)}")

OFFLINE DOCKER TEST CASES:
- GET / returns 200 and contains each featured group's name.
- GET /groups returns 200; with 13+ sample groups page 2 returns 200 and
  page 99 returns 200 with an empty list (not an error).
- GET /group/acme-devs returns 200 for a seeded slug; GET /group/nope
  returns 404.
- The stats on / equal the real database counts.
"""
EOF

cat << 'EOF' > app/templates/public/home.html
<!--
FILE PURPOSE: Landing page (PDR §5.3, Design Plan §2): hero slider,
animated stats, Featured Groups carousel, directory teaser, Request-a-
Project call to action.

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "base.html" %}; {% from "partials/_macros.html" import
   group_card %}.
2. Hero: an Owl Carousel (class owl-carousel, fade transition) with 2-3
   slides over a Stellar parallax background (data-stellar-background-
   ratio="0.5"); headline "Discover the teams building tomorrow", a
   subheadline, and two buttons: "Browse Groups" (url_for public.groups)
   and "Request a Project" (href="#" until P4 — comment this).
3. Stats strip: three counters (Groups, Members, Projects) using elements
   with class number and data-number="{{ stats.groups }}" etc., animated
   by jquery.animateNumber when scrolled into view via Waypoints.
4. "Featured Groups" section: an Owl Carousel of group_card for each item
   in featured_groups.
5. "Explore Groups" section: a 3-column grid of group_card for
   teaser_groups plus a "View all groups" link.
6. Each section gets data-aos="fade-up".
7. Empty-state text when there are no groups: "No groups yet."

DEBUGGING:
<!-- <script>console.log("[DEBUG] home.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The page contains the three stat labels and each data-number equals the
  context value.
- With zero groups the page renders "No groups yet." and no exception.
- Only one element with id="ftco-navbar" exists (base layout not duplicated).
-->
EOF

cat << 'EOF' > app/templates/public/groups_directory.html
<!--
FILE PURPOSE: /groups browsable directory with pagination (live filtering
is added in P5).

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "base.html" %}; import group_card.
2. Page heading "Groups"; a placeholder container
   <div id="directory-filter" data-endpoint="" class="d-none"></div> with a
   comment that P5 fills it with the search box and tag filter.
3. A Bootstrap row (id="directory-results") rendering group_card for each
   group in the paginated object's items, 3 columns on lg, 2 on md, 1
   below md.
4. Pagination control from the page object: previous/next plus page
   numbers, with aria-label="Pagination" and aria-current on the active
   page; hide when only one page exists.
5. Empty state: "No groups match yet."

DEBUGGING:
<!-- <script>console.log("[DEBUG] groups_directory.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- 13 sample groups render 12 cards on page 1 and 1 card on page 2.
- The pagination nav is absent when there is a single page.
- The element with id directory-results exists (P5 depends on it).
-->
EOF

cat << 'EOF' > app/templates/public/group_detail.html
<!--
FILE PURPOSE: One-page-style group profile (PDR §5.3): hero, About, Team,
Tech Stack, Projects, stat strip, Contact form UI (not yet sending).

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "base.html" %}; import member_card and project_card.
2. {% block title %}{{ group.name }} — CodeCrews{% endblock %}.
3. Hero with Stellar parallax using group.cover_image_path, name, tagline,
   and in-page anchor links (About, Team, Tech Stack, Projects, Contact)
   that smooth-scroll.
4. About: description, founded date, location, tech tag pills, member and
   project counts.
5. Team: row of member_card for each member (no bookmark icons).
6. Tech Stack: for each tag in group.tech_tags an animated progress bar
   (class progress-bar, width from a deterministic value derived from the
   tag position — e.g. 90, 80, 70 — documented in a comment) with a label.
7. Projects: grid of project_card; each opens a Magnific Popup showing the
   full description, tags, gallery images with their alt text, and
   GitHub/live links.
8. Stat strip (4 counters): Projects Completed, Members, Years Active
   (from years_active), Total Projects.
9. Blog placeholder: <section id="blog" class="d-none"></section> with a
   comment — filled in P5.
10. Contact: a form card (white surface, text #212529) with name, email,
    subject, message fields and a submit button. Add
    <!-- P4 wires this form to /group/<slug>/contact --> and set
    action="" for now. Include a hidden honeypot input named website
    (display:none) so P4 only needs to validate it.
11. Every image has meaningful alt text.

DEBUGGING:
<!-- <script>console.log("[DEBUG] group_detail.html rendered for {{ group.slug }}");</script> -->

OFFLINE DOCKER TEST CASES:
- GET a seeded group page returns 200 and contains the group name in the
  <title>.
- Each of the five anchor ids (about, team, tech-stack, projects,
  contact) exists.
- A group with zero members and zero projects still renders (empty-state
  text "No members yet." / "No projects yet.").
-->
EOF

cat << 'EOF' > app/templates/partials/navbar.html
<!--
FILE PURPOSE: Sticky navbar — P2 turns the placeholder links into real ones.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep the P0 structure (navbar-brand, burger with aria-label="Toggle
   navigation", #ftco-nav collapse).
2. Home -> url_for('public.index'); Groups -> url_for('public.groups').
3. "Our Members" and "Request a Project" stay href="#" with a comment on
   the milestones that wire them (P5, P4).
4. Add an "active" class to the link matching request.endpoint.
5. (The "Join as a Coder" outlined link is added in P8.)

DEBUGGING:
<!-- <script>console.log("[DEBUG] navbar.html active={{ request.endpoint }}");</script> -->

OFFLINE DOCKER TEST CASES:
- On /groups the Groups link has class "active" and Home does not.
- All four labels still render.
-->
EOF

cat << 'EOF' > app/static/css/style.css
/*
FILE PURPOSE: Base stylesheet — P2 extends it (never replaces) for the
home, directory and group pages.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep every P0 rule and the six --cc-* variables.
2. Add styles for: hero slider (full-height, overlay gradient, centered
   text), .cc-card (dark card, border radius, hover lift), tag pills
   (.cc-tag, amber outline), badges (.cc-badge-featured amber,
   .cc-badge-status variants green/gold), stat counters (.cc-stat large
   number in --cc-color-primary), progress bars for the tech stack,
   section headings with a short amber underline, the group hero with a
   dark overlay, and the white contact form card using
   --cc-color-text-on-light.
3. Responsive rules: card grids collapse to one column below 768px.
4. Visible focus outlines (2px --cc-color-secondary) for links and buttons.

DEBUGGING:
/* console.log("[DEBUG] style.css extended for P2"); */

OFFLINE DOCKER TEST CASES:
- The stylesheet still defines the six --cc-* variables.
- No unclosed braces (valid CSS).
*/
EOF

cat << 'EOF' > app/static/js/main.js
/*
FILE PURPOSE: Base JS — P2 initializes the carousels, parallax, counters
and popups for the public pages.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep the P0 behavior (loader fadeOut, navbar .scrolled after 150px,
   flash auto-dismiss after 5s, AOS init guarded).
2. If $.fn.owlCarousel exists: initialize .hero-carousel (items 1, loop,
   autoplay 5000ms, animateOut "fadeOut", nav false, dots true) and
   .featured-carousel (responsive: 1 item <768px, 2 <992px, 3 above).
3. If $.fn.stellar exists: $.stellar({ horizontalScrolling: false,
   verticalOffset: 40 }).
4. Counters: for each .number element, create a Waypoint (offset "95%",
   handler once) that calls $(el).animateNumber({ number: data-number })
   and then destroys the waypoint.
5. Magnific Popup: initialize .js-project-popup with type "inline" and
   gallery enabled; guard if the plugin is absent.
6. Smooth-scroll for in-page anchor links (a[href^="#"] with a target
   that exists), offset by the navbar height.
7. Expose window.initPublicEffects = function (rootEl) that re-runs AOS
   refresh for injected content (used by P5's live filter).

DEBUGGING:
// console.log("[DEBUG] main.js P2 effects initialized");

OFFLINE DOCKER TEST CASES:
- With the vendor libraries present, .hero-carousel gains the class
  "owl-loaded".
- A .number element with data-number=12 shows 12 after its waypoint fires.
- Calling window.initPublicEffects(document) does not throw when AOS is
  missing.
*/
EOF

cat << 'EOF' > tests/test_public_routes.py
"""
FILE PURPOSE: P2 acceptance tests — "a visitor can browse seeded groups end
to end".

PROMPT FOR LLM IMPLEMENTATION:
1. Add a fixture sample_groups(app) that calls create_sample_data().
2. test_home_200_and_stats(client, sample_groups): GET / is 200 and the
   stat numbers equal the database counts.
3. test_home_empty_state(client): with no data GET / is 200 and shows
   "No groups yet."
4. test_groups_directory_pagination(client, sample_groups): page 1 has up
   to 12 cards; ?page=99 returns 200 with an empty list.
5. test_group_detail_ok_and_404(client, sample_groups): a known slug is
   200 and has the five section ids; an unknown slug is 404.
6. test_group_detail_blank_member_project_lists(client, app): a group with
   no members/projects renders its empty states.
7. test_resume_icon_only_when_resume_exists(client, sample_groups): the
   page for a group with a resume contains "Download" in an aria-label,
   and a group without resumes does not.
8. test_every_image_has_alt(client, sample_groups): parse the group page
   HTML and assert every <img> has a non-empty alt.
9. test_no_bookmark_markup(client, sample_groups): the HTML contains no
   "bookmark" or "Saved (" text (feature is out of scope).

DEBUGGING:
# print("[DEBUG] running P2 public route tests")

OFFLINE DOCKER TEST CASES:
- All tests pass offline against the SQLite test database.
"""
EOF

git add -A
git commit -q -m "P2 seed: public group directory placeholders (Abhishek)"
git push -u origin task-abhishek-phase2-group-directory || echo "WARNING: could not push task-abhishek-phase2-group-directory."

echo ""
echo "====================================================="
echo "Milestone P2 Seeded Successfully!"
echo "NEXT STEPS (Abhishek):"
echo "1. Feed the seeded files to your LLM (code-implementer) to generate the code."
echo "2. Run: docker-compose -f docker-compose.test.yml run --rm web pytest"
echo "3. Try it: docker-compose up --build; docker-compose exec web python seed.py --sample-only"
echo "4. Commit in logical chunks, open a PR into 'phase2', review and merge."
echo "5. If tests pass: git checkout MAIN && git merge phase2, then tag the release."
echo "6. Execute P3.sh."
echo "====================================================="
