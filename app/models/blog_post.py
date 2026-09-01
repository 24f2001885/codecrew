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
