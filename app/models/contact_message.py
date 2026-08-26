"""
FILE PURPOSE: ContactMessage model stub (TDR §4 table: contact_messages)
— group_id is NOT NULL as of v2, no more nullable "suggestion" case.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class ContactMessage(db.Model) with __tablename__ = "contact_messages".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   group_id FK (NOT NULL), name, email, subject, message, is_read, and
   created_at land in P1, with the submit flow built out in P4.
4. __repr__ returning "<ContactMessage {id}>".

DEBUGGING:
# print(f"[DEBUG] ContactMessage stub registered: {ContactMessage.__tablename__}")

OFFLINE DOCKER TEST CASES:
- ContactMessage.__tablename__ == "contact_messages".
- "contact_messages" is present in db.metadata.tables after the app is
  created.
"""
