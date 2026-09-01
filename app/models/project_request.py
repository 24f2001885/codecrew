"""
FILE PURPOSE: ProjectRequest model — full columns (TDR §4 table:
project_requests), platform-wide and new in v2 (not tied to a Group at
submission time).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions, and Enum
   from sqlalchemy (or db.Enum).
2. class ProjectRequest(db.Model) with __tablename__ = "project_requests".
3. Columns exactly per TDR §4: id (UUID PK); name (String(120), not
   null); email (String(255), not null); company (String(150),
   nullable); project_type (Enum: "web_app", "mobile_app",
   "desktop_software", "api_backend", "other"; not null); budget_range
   (String(80), nullable); timeline (String(80), nullable); description
   (Text, not null); attachment_path (String(255), nullable); status
   (Enum: "new", "in_review", "contacted", "closed"; not null, default
   "new"); assigned_group_id (String(36) FK -> groups.id, nullable,
   ondelete="SET NULL"); created_at (DateTime, not null, default now,
   indexed — "for inbox sort"); updated_at (DateTime, not null, default
   now, on-update now).
4. assigned_group = db.relationship("Group") (no backref needed — Group
   doesn't need a reverse collection of requests per the PDR's data
   model description in §8).
5. __repr__ returning "<ProjectRequest from {self.name} ({self.status})>".

DEBUGGING:
# print(f"[DEBUG] ProjectRequest full model registered: {ProjectRequest.__tablename__}")

OFFLINE DOCKER TEST CASES:
- ProjectRequest.status defaults to "new" when not set.
- A ProjectRequest can be created with assigned_group_id=None (platform-
  wide submissions don't require a Group at submission time, per PDR
  §8/TDR §4).
- Deleting the assigned Group sets assigned_group_id to NULL on the
  ProjectRequest rather than deleting the request row (ON DELETE SET
  NULL, not CASCADE — distinct from every other FK in this schema).
"""
