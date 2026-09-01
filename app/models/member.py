"""
FILE PURPOSE: Member model — full columns (TDR §4 table: members),
including the v2-added resume_pdf field (PDR §5.4).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions.
2. class Member(db.Model) with __tablename__ = "members".
3. Columns exactly per TDR §4: id (UUID PK); group_id (String(36) FK ->
   groups.id, not null, indexed, ondelete="CASCADE"); name
   (String(120), not null); role (String(120), nullable); photo_path
   (String(255), nullable); bio (Text, nullable); skill_tags (JSON, not
   null, default list); github_url / linkedin_url / twitter_url
   (String(255), nullable each); resume_pdf (String(255), nullable —
   "added in v2" per TDR §4); display_order (Integer, not null, default
   0); created_at (DateTime, not null, default now).
4. No explicit relationship() declared here — Group.members (backref)
   from group.py already provides the reverse side.
5. __repr__ returning "<Member {self.name}>".

DEBUGGING:
# print(f"[DEBUG] Member full model registered: {Member.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Member.skill_tags defaults to [] when not set at construction.
- A Member with resume_pdf=None round-trips correctly (nullable, not
  required — PDR §5.4: uploads are opt-in per member).
- Creating a Member with a group_id that doesn't exist in `groups`
  raises an IntegrityError (FK enforcement) once SQLite foreign_keys
  pragma / Postgres FK is active.
"""
