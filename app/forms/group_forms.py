from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, FileField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, URL
from app.forms import parse_tag_string


class GroupForm(FlaskForm):
    name = StringField("Group Name", validators=[DataRequired(message="Group name is required."), Length(min=2, max=120)])
    tagline = StringField("Tagline", validators=[Optional(), Length(max=200)])
    description = TextAreaField("Description", validators=[Optional()])
    founded_year = IntegerField("Founded Year", validators=[Optional()])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    tech_tags = StringField("Tech Stack (comma separated)", validators=[Optional()])
    github_url = URLField("GitHub URL", validators=[Optional(), URL(message="Invalid URL format.")])
    website_url = URLField("Website URL", validators=[Optional(), URL(message="Invalid URL format.")])
    linkedin_url = URLField("LinkedIn URL", validators=[Optional(), URL(message="Invalid URL format.")])
    logo = FileField("Logo Image", validators=[Optional()])
    cover_image = FileField("Cover Banner", validators=[Optional()])
    featured = BooleanField("Featured Group")
    submit = SubmitField("Save Group")

    def parse_tags(self):
        # Extract pure tag names even if percentages like python:95 are provided
        raw = self.tech_tags.data or ""
        tags = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            name = part.split(":", 1)[0].strip().lower()
            if name and name not in tags:
                tags.append(name)
        return tags

    def parse_tags_with_levels(self):
        raw = self.tech_tags.data or ""
        tags = []
        levels = {}
        for idx, part in enumerate(raw.split(",")):
            part = part.strip()
            if not part:
                continue
            if ":" in part:
                name, val = part.split(":", 1)
                name = name.strip().lower()
                try:
                    lvl = int(val.strip())
                    lvl = max(10, min(100, lvl))
                except ValueError:
                    lvl = max(50, 95 - (idx * 5))
            else:
                name = part.lower()
                lvl = max(50, 95 - (idx * 5))
            if name and name not in tags:
                tags.append(name)
                levels[name] = lvl
        return tags, levels
