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
