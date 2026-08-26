"""
FILE PURPOSE: ProjectRequest model stub (TDR §4 table: project_requests)
— platform-wide, new in v2.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class ProjectRequest(db.Model) with __tablename__ = "project_requests".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0; name,
   email, company, project_type enum, budget_range, timeline, description,
   attachment_path, status enum, assigned_group_id FK, and timestamps land
   in P1, with the submit/inbox flow built out in P4.
4. __repr__ returning "<ProjectRequest {id}>".

DEBUGGING:
# print(f"[DEBUG] ProjectRequest stub registered: {ProjectRequest.__tablename__}")

OFFLINE DOCKER TEST CASES:
- ProjectRequest.__tablename__ == "project_requests".
- "project_requests" is present in db.metadata.tables after the app is
  created.
"""
