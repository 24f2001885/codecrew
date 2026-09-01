"""
FILE PURPOSE: BlogPost model stub (TDR §4 table: blog_posts) — per-group,
per the resolved PDR §12 / TDR §4 decision, not platform-wide.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class BlogPost(db.Model) with __tablename__ = "blog_posts".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   group_id FK, title, slug, content, cover_image_path, published_at,
   tags, and created_at land in P1 (schema), with public rendering built
   out in P5.
4. __repr__ returning "<BlogPost {id}>".

DEBUGGING:
# print(f"[DEBUG] BlogPost stub registered: {BlogPost.__tablename__}")

OFFLINE DOCKER TEST CASES:
- BlogPost.__tablename__ == "blog_posts".
- "blog_posts" is present in db.metadata.tables after the app is created.
"""
"""FILE PURPOSE: BlogPost model stub (TDR §4 table: blog_posts) — per-group,
per the resolved PDR §12 / TDR §4 decision, not platform-wide.
"""

import uuid
from app.extensions import db


class BlogPost(db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    def __repr__(self) -> str:
        return f"<BlogPost {self.id}>"


# DEBUGGING:
# print(f"[DEBUG] BlogPost stub registered: {BlogPost.__tablename__}")