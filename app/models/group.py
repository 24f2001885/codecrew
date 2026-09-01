"""
FILE PURPOSE: Group model — full columns (TDR §4 table: groups), the
central entity of the platform. Relationships to Member/Project/
BlogPost/ContactMessage/ProjectRequest are declared here since Group is
the "one" side of every one-to-many in the schema.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions.
2. class Group(db.Model) with __tablename__ = "groups".
3. Columns exactly per TDR §4: id (UUID PK); name (String(120), not
   null); slug (String(140), unique, not null, indexed); tagline
   (String(200), nullable); description (Text, nullable); logo_path
   (String(255), nullable); cover_image_path (String(255), nullable);
   founded_date (Date, nullable); location (String(120), nullable);
   tech_tags (JSON, not null, default list); social_links (JSON, not
   null, default dict); featured (Boolean, not null, default False);
   created_at / updated_at (DateTime, not null, default now, updated_at
   also on-update now).
4. Relationships: members = db.relationship("Member", backref="group",
   cascade="all, delete-orphan"); projects = db.relationship("Project",
   backref="group", cascade="all, delete-orphan"); blog_posts =
   db.relationship("BlogPost", backref="group", cascade="all,
   delete-orphan"); contact_messages = db.relationship("ContactMessage",
   backref="group", cascade="all, delete-orphan") — matching the FK
   ON DELETE CASCADE behavior specified in TDR §4/§5 (deleting a group
   cascades to its members/projects/blog/messages).
5. __repr__ returning "<Group {self.name}>".

DEBUGGING:
# print(f"[DEBUG] Group full model registered: {Group.__tablename__}")

OFFLINE DOCKER TEST CASES:
- A Group's `tech_tags` and `social_links` default to [] and {}
  respectively when not explicitly set at construction time.
- Deleting a Group cascades to its related Member/Project rows in a
  round-trip test (create group + member, delete group, assert member
  row is also gone).
- `slug` rejects a duplicate value at the DB level.
"""
