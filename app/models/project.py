"""
FILE PURPOSE: Project model stub (TDR §4 table: projects).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class Project(db.Model) with __tablename__ = "projects".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   group_id FK, title, slug, description, gallery_images, tech_tags,
   URLs, status enum, featured, and created_at land in P1.
4. __repr__ returning "<Project {id}>".

DEBUGGING:
# print(f"[DEBUG] Project stub registered: {Project.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Project.__tablename__ == "projects".
- "projects" is present in db.metadata.tables after the app is created.
"""
"""FILE PURPOSE: Project model stub (TDR §4 table: projects)."""

import uuid
from app.extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    def __repr__(self) -> str:
        return f"<Project {self.id}>"


# DEBUGGING:
# print(f"[DEBUG] Project stub registered: {Project.__tablename__}")