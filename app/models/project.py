"""
FILE PURPOSE: Project model — full columns (TDR §4 table: projects).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions, and Enum
   from sqlalchemy (or db.Enum).
2. class Project(db.Model) with __tablename__ = "projects".
3. Columns exactly per TDR §4: id (UUID PK); group_id (String(36) FK ->
   groups.id, not null, indexed, ondelete="CASCADE"); title
   (String(150), not null); slug (String(170), not null — unique
   together with group_id via a UniqueConstraint("group_id", "slug"));
   description (Text, nullable); gallery_images (JSON, not null,
   default list); tech_tags (JSON, not null, default list); github_url /
   live_url (String(255), nullable each); status (Enum: "planned",
   "in_progress", "completed", "archived"; not null, default
   "completed"); featured (Boolean, not null, default False); created_at
   (DateTime, not null, default now).
4. __table_args__ = (db.UniqueConstraint("group_id", "slug",
   name="uq_project_group_slug"),).
5. __repr__ returning "<Project {self.title}>".

DEBUGGING:
# print(f"[DEBUG] Project full model registered: {Project.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Project.status defaults to "completed" when not set.
- Two Projects with the same slug under different group_id values are
  both allowed (uniqueness is scoped per-group, not global).
- Two Projects with the same slug under the SAME group_id raise an
  IntegrityError.
"""
