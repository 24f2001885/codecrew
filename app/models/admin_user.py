"""
FILE PURPOSE: AdminUser model stub (TDR §4 table: admin_users).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class AdminUser(db.Model) with __tablename__ = "admin_users".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   username/password_hash/created_at land in P1.
4. __repr__ returning "<AdminUser {id}>".

DEBUGGING:
# print(f"[DEBUG] AdminUser stub registered: {AdminUser.__tablename__}")

OFFLINE DOCKER TEST CASES:
- AdminUser.__tablename__ == "admin_users".
- "admin_users" is present in db.metadata.tables after the app is created.
"""
import uuid
from app.extensions import db


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    def __repr__(self) -> str:
        return f"<AdminUser {self.id}>"


# DEBUGGING:
# print(f"[DEBUG] AdminUser stub registered: {AdminUser.__tablename__}")