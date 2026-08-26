"""
FILE PURPOSE: Member model stub (TDR §4 table: members).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class Member(db.Model) with __tablename__ = "members".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   group_id FK, name, role, photo_path, bio, skill_tags, social URLs,
   resume_pdf, display_order, and created_at land in P1.
4. __repr__ returning "<Member {id}>".

DEBUGGING:
# print(f"[DEBUG] Member stub registered: {Member.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Member.__tablename__ == "members".
- "members" is present in db.metadata.tables after the app is created.
"""
