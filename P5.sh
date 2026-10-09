#!/usr/bin/env bash
# P5.sh
# CodeCrews — Milestone P5: Members Directory, Search/Filter & Blog
#
# Developer: Abhishek (Team Lead and sole developer)
#
# Goal (Master Project Blueprint v2): every interactive public feature is
# live — the platform-wide Members directory, the shared live search/filter
# for Groups and Members, resume downloads, member profile popups, and the
# per-group blog.
#
# This script contains zero application logic; every file is a heredoc
# holding a PROMPT for an LLM (code-implementer), on ONE task branch.
#
# Source docs: master-project-blueprint-v2.md §3 (P5), PDR v2 §5.4/§5.6/
# §5.7, TDR v2 §3.2 (search engine) and §5, Design Plan v2 §2/§4.2.

set -e

echo "====================================================="
echo "CodeCrews — P5: Members Directory, Search/Filter & Blog"
echo "Developer: Abhishek"
echo "====================================================="

echo ""
echo "--- Phase 5 initialization ---"
git checkout MAIN
git pull origin MAIN || echo "WARNING: could not pull MAIN (offline — continuing)."

if git show-ref --quiet refs/heads/phase5-seed; then
    echo "phase5-seed already exists — skipping."
else
    git checkout -b phase5-seed MAIN
fi
if git show-ref --quiet refs/heads/phase5; then
    echo "phase5 already exists — skipping."
else
    git checkout -b phase5 phase5-seed
fi
git push -u origin phase5-seed || echo "WARNING: could not push phase5-seed."
git push -u origin phase5 || echo "WARNING: could not push phase5."

git checkout phase5
mkdir -p app/forms app/services app/routes app/templates/admin app/templates/public
mkdir -p app/static/js app/static/css tests
git add -A
git commit -q -m "P5: skeleton verification" || echo "Nothing to commit."
git push origin phase5 || echo "WARNING: could not push phase5."

echo ""
echo "--- Creating task-abhishek-phase5-members-search-blog ---"
git checkout -b task-abhishek-phase5-members-search-blog phase5

cat << 'EOF' > app/services/search.py
"""
FILE PURPOSE: The shared filter engine behind /api/groups and /api/members
(TDR v2 §3.2). One implementation, two entities, two database dialects.

PROMPT FOR LLM IMPLEMENTATION:
1. def build_filtered_query(model, query_str, tag, extra_filters=None):
   - Start from model.query.
   - Free text: if query_str is non-empty, strip and match
     case-insensitively with ilike(f"%{term}%") combined via or_() over
     Group.name + Group.tagline, or Member.name + Member.role. Escape the
     LIKE wildcards % and _ in user input.
   - extra_filters is a dict; support {"group_slug": slug} for members by
     joining Group and filtering Group.slug == slug.
   - Tag filter (tag is Group.tech_tags or Member.skill_tags): lowercase
     the incoming tag. If db.engine.dialect.name == "postgresql" use JSON
     containment on a lowercased text cast; otherwise (SQLite) fetch the
     candidate rows with the other filters applied, bounded to 2000 rows,
     filter in Python where the lowercased stored tag list contains the
     tag, and return a list-backed pagination (see step 3).
2. Stable ordering: Group by name asc; Member by name asc.
3. def paginate(query_or_list, page, per_page=12): returns a dict
   {"items": [...], "page": page, "total_pages": n, "total_count": c}.
   Clamp page to >= 1. A page beyond the last returns empty items with the
   real total_pages. Works for both a SQLAlchemy query and a Python list.
4. def search_groups(q, tag, page) and def search_members(q, group_slug,
   skill, page) call build_filtered_query and paginate; they are the only
   functions routes call.
5. Edge cases: empty q and tag -> the full paginated collection; an
   unmatched tag -> items [] and total_count 0 (never an error); tags are
   compared case-insensitively.

DEBUGGING:
# print(f"[DEBUG] search dialect={db.engine.dialect.name} q={q!r} tag={tag!r} -> {total} rows")

OFFLINE DOCKER TEST CASES:
- search_groups("", "", 1) returns every group (up to per_page).
- search_groups("ACME", "", 1) matches "acme-devs" regardless of case.
- A tag "React" matches a group stored with ["react"].
- A tag that matches nothing returns items [] and total_count 0.
- page=99 returns empty items and total_pages >= 1.
- search_members with group_slug returns only that group's members.
- A search term containing "%" does not match everything.
"""
EOF

cat << 'EOF' > app/routes/api.py
"""
FILE PURPOSE: JSON endpoints for live filtering (TDR v2 §5):
GET /api/groups and GET /api/members. Unauthenticated, read-only.

PROMPT FOR LLM IMPLEMENTATION:
1. api_bp = Blueprint("api", __name__, url_prefix="/api").
2. GET /api/groups with query q, tag, page -> services.search.search_groups;
   respond with {"items": [GroupCard...], "page", "total_pages",
   "total_count"}. GroupCard fields: slug, name, tagline, logo_path,
   cover_image_path, tech_tags, featured, member_count, project_count.
   Also include "html": the rendered markup of the group_card macro for
   each item joined together, so the frontend can inject it without
   rebuilding templates in JS (render via a small template that imports
   the macro).
3. GET /api/members with query q, group, skill, page ->
   search_members; MemberCard fields: id, name, role, photo_path, bio
   (full), skill_tags, github_url, linkedin_url, twitter_url,
   has_resume (bool), resume_pdf (path or null), group_name, group_slug,
   projects (list of {title, slug} for projects credited to the member's
   group — see comment), plus "html" rendered via member_card.
   Never include anything from ContactMessage, ProjectRequest or any coder
   table.
4. Validate page: non-integer or < 1 becomes 1; cap per_page at 12 (no
   client-supplied per_page).
5. Responses are JSON with Cache-Control: no-store off; allow short
   caching (max-age=30) is optional — keep it simple: no caching header.
6. Comment: "projects credited to the member" is the group's projects in
   this phase because the schema has no member-project link.

DEBUGGING:
# print(f"[DEBUG] /api/members q={q!r} group={group!r} skill={skill!r} page={page}")

OFFLINE DOCKER TEST CASES:
- GET /api/groups returns 200 JSON with items, page, total_pages,
  total_count.
- GET /api/groups?tag=nonexistent returns total_count 0 and 200.
- GET /api/members?group=<slug> returns only that group's members.
- GET /api/members?page=abc is treated as page 1.
- The JSON for members contains has_resume true only for members with a
  resume and never contains "email".
"""
EOF

cat << 'EOF' > app/routes/public.py
"""
FILE PURPOSE: Public blueprint — P5 adds /members and live-filter hooks.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep index, groups and group_detail from P2/P4.
2. groups(): accept q, tag, page; use services.search.search_groups so the
   first server-rendered page already reflects the query string (the page
   is shareable); pass the result dict to the template.
3. GET /members (endpoint "members"): accept q, group, skill, page; use
   search_members; also pass the list of all groups (slug, name) for the
   group filter dropdown. Render "public/members_directory.html".
4. group_detail(): add the group's published blog posts (published_at not
   null and <= now, newest first, max 3 on the page) as blog_posts.
5. index(): the directory teaser keeps using the first 6 groups.

DEBUGGING:
# print(f"[DEBUG] GET /members q={q!r} group={group!r} skill={skill!r}")

OFFLINE DOCKER TEST CASES:
- GET /members returns 200 and lists members from every group.
- GET /members?group=acme-devs shows only that group's members.
- GET /groups?q=acme shows the matching group first.
- Draft blog posts (published_at NULL) never appear on the group page.
"""
EOF

cat << 'EOF' > app/templates/public/members_directory.html
<!--
FILE PURPOSE: Platform-wide Members directory (PDR §5.4): live-filtered
card grid with resume buttons and a profile popup.

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "base.html" %}; import member_card.
2. Filter bar: a text input (id="filter-q", aria-label "Search members"),
   a group <select> (id="filter-group", "All groups" + each group), and a
   skill text input (id="filter-skill"). Wrap in
   <div id="directory-filter" data-endpoint="{{ url_for('api.members') }}"
   data-kind="members">.
3. Results container id="directory-results" (row of member_card for the
   server-rendered first page) and a status line (id="directory-status",
   aria-live="polite") showing "N members" or "No members match your
   search."
4. Pagination nav (id="directory-pagination") rendered server-side and
   updated by JS.
5. Magnific Popup content: each card links (class js-member-popup) to a
   hidden inline block per member holding the full bio, social links, the
   resume link (only when present, aria-label naming the member), and the
   list of the group's projects. (The API's "projects" list fills this when
   cards are injected.)

DEBUGGING:
<!-- <script>console.log("[DEBUG] members_directory.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The three filter controls and results container exist with the ids
  above.
- The first page renders without JavaScript (server-rendered cards).
- A member without a resume shows no resume control in the popup.
-->
EOF

cat << 'EOF' > app/templates/public/groups_directory.html
<!--
FILE PURPOSE: /groups — P5 fills the filter placeholder P2 left.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep P2 markup and the #directory-results container.
2. Replace the placeholder with a filter bar: text input id="filter-q"
   (aria-label "Search groups") and a tag input id="filter-tag", inside
   <div id="directory-filter" data-endpoint="{{ url_for('api.groups') }}"
   data-kind="groups">.
3. Add the aria-live status line and keep server-rendered pagination;
   pre-fill the inputs from the query string.

DEBUGGING:
<!-- <script>console.log("[DEBUG] groups_directory filter wired");</script> -->

OFFLINE DOCKER TEST CASES:
- The filter bar exists; typing is handled by directory-filter.js.
- GET /groups?q=acme pre-fills the search input with "acme".
-->
EOF

cat << 'EOF' > app/static/js/directory-filter.js
/*
FILE PURPOSE: One live-filter script shared by /groups and /members
(PDR §5.6, TDR v2 §7).

PROMPT FOR LLM IMPLEMENTATION:
1. Wrap in an IIFE using jQuery. Find #directory-filter; exit if absent.
   Read data-endpoint and data-kind ("groups" or "members").
2. State is plain variables: q, tag/skill, group, page. Initialize them
   from the current URL query string.
3. Debounce keyup on #filter-q, #filter-tag/#filter-skill and change on
   #filter-group by 250 ms. Each change resets page to 1.
4. Fetch endpoint?q=...&tag=...|&skill=...&group=...&page=... with
   $.getJSON; ignore stale responses (use an incrementing request id).
5. Render: fade out #directory-results (150 ms), replace its html with
   response.html, fade in, call AOS.refresh() (guarded) and
   window.initPublicEffects(container) from main.js, rebuild the popup
   bindings for member cards.
6. Update #directory-status ("12 groups" / "No groups match your
   search."), rebuild #directory-pagination from page/total_pages, and
   update the URL with history.replaceState so filtered views are
   shareable.
7. On a failed request show "Could not load results. Please try again."
   in the status line (no alerts).

DEBUGGING:
// console.log("[DEBUG] directory-filter request", params);

OFFLINE DOCKER TEST CASES:
- With a mocked $.getJSON returning two items, #directory-results shows
  two cards and the status line says "2 members".
- Typing quickly triggers one request (debounce).
- A response with items [] shows the "no match" message.
- After injection, AOS.refresh is called once.
*/
EOF

cat << 'EOF' > app/static/js/main.js
/*
FILE PURPOSE: Base JS — P5 adds the member profile popup.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep every P0/P2 behavior.
2. Delegated click handler for .js-member-popup that opens a Magnific
   Popup (type "inline") with the matching hidden member block; works for
   cards injected later by directory-filter.js (use $(document).on).
3. initPublicEffects(root) must also rebind nothing twice (guard with a
   data attribute).
4. Resume buttons need no JS (plain links with download behavior).

DEBUGGING:
// console.log("[DEBUG] main.js P5 member popup bound");

OFFLINE DOCKER TEST CASES:
- Clicking an injected member card opens the popup with that member's
  name.
- Calling initPublicEffects twice does not duplicate handlers.
*/
EOF

cat << 'EOF' > app/forms/blog_forms.py
"""
FILE PURPOSE: Admin form for per-group blog posts (PDR §5.7).

PROMPT FOR LLM IMPLEMENTATION:
1. class BlogPostForm(FlaskForm): group_id (SelectField of groups,
   DataRequired — posts always belong to exactly one group); title
   (DataRequired, Length 3-200); content (TextAreaField, DataRequired,
   Length min 20); tags (comma separated, Optional); cover_image
   (FileField, Optional, image extensions); published (BooleanField
   "Publish now"); submit.
2. Publishing logic is in the route: published True sets published_at to
   now if empty; False sets it to None (draft).
3. Reuse the shared tag parser rules (max 20 tags, 30 chars each).

DEBUGGING:
# print(f"[DEBUG] BlogPostForm group={self.group_id.data} published={self.published.data}")

OFFLINE DOCKER TEST CASES:
- Missing group fails validation.
- A 5-character content fails validation.
"""
EOF

cat << 'EOF' > app/routes/admin.py
"""
FILE PURPOSE: Admin blueprint — P5 adds Blog CRUD (TDR v2 §5).

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything from P3/P4 and the guard.
2. GET /admin/blog (query page, optional group_id; 15 per page; columns
   title, group, status pill Published green / Draft gold, date, actions);
   GET/POST /admin/blog/new; GET/POST /admin/blog/<id>/edit; POST
   /admin/blog/<id>/delete (confirm modal, POST only).
3. Slug unique per group via services.slugs.unique_slug with scope
   {"group_id": gid}; cover image via services.uploads (subfolder
   "covers"); published flag sets/clears published_at.
4. Blog posts are admin-only (coders cannot manage them — PDR D6).
5. Dashboard: add draft and published post counts.

DEBUGGING:
# print(f"[DEBUG] admin blog saved id={post.id} published={post.published_at is not None}")

OFFLINE DOCKER TEST CASES:
- Creating a post for a group publishes it on that group's page when
  "Publish now" is checked, and hides it when unchecked.
- Two posts with the same title in one group get different slugs; in
  different groups both keep the plain slug.
- Deleting is POST only.
"""
EOF

cat << 'EOF' > app/templates/admin/blog_list.html
<!--
FILE PURPOSE: Blog posts list (admin).

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "admin/admin_base.html" %}; title "Blog".
2. Group filter dropdown; table with title, group, status pill (text +
   color), published/created date, Edit and Delete (confirm modal with
   aria-labels naming the post).
3. "New post" button; pagination; empty state "No posts yet."

DEBUGGING:
<!-- <script>console.log("[DEBUG] blog_list.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- Draft and Published pills show text.
- Filtering by group_id limits rows.
-->
EOF

cat << 'EOF' > app/templates/admin/blog_form.html
<!--
FILE PURPOSE: Create/edit blog post.

PROMPT FOR LLM IMPLEMENTATION:
1. Multipart form with csrf, group select, title, content textarea, tags,
   cover image (with current thumbnail and alt text on edit), "Publish
   now" checkbox.
2. Inline errors with role="alert".

DEBUGGING:
<!-- <script>console.log("[DEBUG] blog_form.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The form has a csrf_token and enctype multipart/form-data.
-->
EOF

cat << 'EOF' > app/templates/public/group_detail.html
<!--
FILE PURPOSE: Group detail — P5 fills the blog section.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything from P2/P4.
2. Replace the hidden #blog placeholder with a visible section only when
   blog_posts is not empty: heading "Dev Log", a 3-column card grid
   (stacks on mobile) with cover image (alt = post title), title, date,
   a 160-character excerpt, tags; each card opens a Magnific Popup showing
   the full content.
3. Render post content as escaped text with paragraph breaks (no |safe).
4. Add "Blog" to the in-page anchor links only when posts exist.

DEBUGGING:
<!-- <script>console.log("[DEBUG] group_detail blog section: {{ blog_posts|length }} posts");</script> -->

OFFLINE DOCKER TEST CASES:
- With three published posts three cards render; with none the section is
  absent.
- HTML tags typed into a post body appear escaped.
-->
EOF

cat << 'EOF' > app/templates/partials/navbar.html
<!--
FILE PURPOSE: Navbar — P5 links "Our Members".

PROMPT FOR LLM IMPLEMENTATION:
1. Keep earlier links and active-state logic.
2. "Our Members" -> url_for('public.members').

DEBUGGING:
<!-- <script>console.log("[DEBUG] navbar P5");</script> -->

OFFLINE DOCKER TEST CASES:
- The Our Members link resolves to /members and is active there.
-->
EOF

cat << 'EOF' > app/__init__.py
"""
FILE PURPOSE: Application factory — P5 registers the API blueprint.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything from earlier milestones.
2. Register api_bp from app/routes/api.py.
3. Exempt the two GET-only API routes from rate limiting but apply a
   generous default limit "120 per minute" per IP to the api blueprint.
4. Update the comment: remaining blueprints join/coder_auth/coder (P7, P8).

DEBUGGING:
# print("[DEBUG] blueprints now include api")

OFFLINE DOCKER TEST CASES:
- app.url_map contains /api/groups and /api/members.
- The 121st request in a minute to /api/groups returns 429 when the
  limiter is enabled in the test config.
"""
EOF

cat << 'EOF' > tests/test_search_api.py
"""
FILE PURPOSE: P5 tests — shared search engine and both API endpoints.

PROMPT FOR LLM IMPLEMENTATION:
1. Unit tests for services/search.py cases listed in its seed prompt.
2. API tests: response shape for /api/groups and /api/members; filters by
   q, tag, group, skill; pagination clamping; non-integer page.
3. test_tag_matching_is_case_insensitive.
4. test_percent_sign_in_query_is_escaped.
5. test_members_api_never_exposes_private_fields: assert the JSON text
   contains none of "email", "password", "internal_notes", "message".
6. test_sqlite_python_filter_path_used (assert dialect is sqlite in tests)
   and add a clearly marked test that is skipped unless
   TEST_DATABASE_URL points at PostgreSQL, checking the containment path
   returns the same results.
7. test_filtered_views_share_state_via_query_string: GET /members?skill=x
   renders only matching members server-side.

DEBUGGING:
# print("[DEBUG] running search API tests")

OFFLINE DOCKER TEST CASES:
- All pass offline on SQLite; the Postgres test is skipped by default.
"""
EOF

cat << 'EOF' > tests/test_members_directory.py
"""
FILE PURPOSE: P5 tests — Members page behavior.

PROMPT FOR LLM IMPLEMENTATION:
1. test_members_page_lists_members_from_all_groups.
2. test_resume_button_only_when_resume_exists_and_has_aria_label.
3. test_group_badge_links_to_group_page.
4. test_member_without_skill_tags_renders_without_empty_tag_list.
5. test_members_page_images_have_alt.
6. test_members_page_works_without_js (server-rendered first page).

DEBUGGING:
# print("[DEBUG] running members directory tests")

OFFLINE DOCKER TEST CASES:
- All pass offline.
"""
EOF

cat << 'EOF' > tests/test_blog_crud.py
"""
FILE PURPOSE: P5 tests — per-group blog.

PROMPT FOR LLM IMPLEMENTATION:
1. test_blog_requires_admin_login.
2. test_create_published_post_appears_on_group_page_only.
3. test_draft_hidden_from_public.
4. test_slug_unique_within_group_only.
5. test_group_id_required (blog is per-group, never platform-wide).
6. test_delete_is_post_only_and_cascades_with_group_delete.
7. test_post_content_is_escaped_on_public_page.

DEBUGGING:
# print("[DEBUG] running blog CRUD tests")

OFFLINE DOCKER TEST CASES:
- All pass offline.
"""
EOF

git add -A
git commit -q -m "P5 seed: members directory, search/filter and blog placeholders (Abhishek)"
git push -u origin task-abhishek-phase5-members-search-blog || echo "WARNING: could not push task-abhishek-phase5-members-search-blog."

echo ""
echo "====================================================="
echo "Milestone P5 Seeded Successfully!"
echo "NEXT STEPS (Abhishek):"
echo "1. Feed the seeded files to your LLM (code-implementer) to generate the code."
echo "2. Run: docker-compose -f docker-compose.test.yml run --rm web pytest"
echo "3. Commit in logical chunks, open a PR into 'phase5', review and merge."
echo "4. If tests pass: git checkout MAIN && git merge phase5, then tag the release."
echo "5. Execute P6.sh."
echo "====================================================="
