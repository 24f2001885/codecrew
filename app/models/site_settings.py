"""
FILE PURPOSE: SiteSettings model stub (TDR §4 table: site_settings) —
singleton row, Integer PK always 1 (NOT a UUID like the other models).

PROMPT FOR LLM IMPLEMENTATION:
1. Import db from app.extensions (no uuid needed here).
2. class SiteSettings(db.Model) with __tablename__ = "site_settings".
3. id = db.Column(db.Integer, primary_key=True, default=1) — only the
   primary key in P0; hero/footer/SEO fields and stats_override land in
   P1, with the /admin/settings screen built out in P6.
4. __repr__ returning "<SiteSettings {id}>".

DEBUGGING:
# print(f"[DEBUG] SiteSettings stub registered: {SiteSettings.__tablename__}")

OFFLINE DOCKER TEST CASES:
- SiteSettings.__tablename__ == "site_settings".
- "site_settings" is present in db.metadata.tables after the app is
  created.
"""
