"""
FILE PURPOSE: Group model stub (TDR §4 table: groups) — the central
entity of the platform.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class Group(db.Model) with __tablename__ = "groups".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0; name,
   slug, tagline, description, image paths, tech_tags, social_links,
   featured, and timestamps land in P1, along with relationships to
   Member/Project/BlogPost/ContactMessage.
4. __repr__ returning "<Group {id}>".

DEBUGGING:
# print(f"[DEBUG] Group stub registered: {Group.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Group.__tablename__ == "groups".
- "groups" is present in db.metadata.tables after the app is created.
"""
