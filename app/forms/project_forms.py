from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, SubmitField, URLField, MultipleFileField
from wtforms.validators import DataRequired, Length, Optional, URL, ValidationError
from app.forms import parse_tag_string

ALLOWED_STATUSES = [
    ("planned", "Planned"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("archived", "Archived"),
]


class ProjectForm(FlaskForm):
    title = StringField("Project Title", validators=[DataRequired(message="Project title is required."), Length(min=2, max=150)])
    summary = StringField("Short Summary", validators=[Optional(), Length(max=300)])
    description = TextAreaField("Full Description", validators=[Optional()])
    tech_tags = StringField("Tech Stack (comma separated)", validators=[Optional()])
    github_url = URLField("GitHub URL", validators=[Optional(), URL(message="Invalid URL format.")])
    live_url = URLField("Live Demo URL", validators=[Optional(), URL(message="Invalid URL format.")])
    status = SelectField(
        "Project Status",
        choices=ALLOWED_STATUSES,
        default="completed",
        validators=[DataRequired(message="Status is required.")],
    )
    featured = BooleanField("Featured Project")
    gallery_files = MultipleFileField("Screenshots", validators=[Optional()])
    gallery_alts = TextAreaField("Image Descriptions (one per line, matching uploaded images)", validators=[Optional()])
    submit = SubmitField("Save Project")

    def validate_status(self, field):
        valid_keys = [k for k, _ in ALLOWED_STATUSES]
        if field.data not in valid_keys:
            raise ValidationError(f"Invalid status '{field.data}'. Allowed: {', '.join(valid_keys)}")

    def validate(self, extra_validators=None):
        initial_valid = super().validate(extra_validators=extra_validators)
        if not initial_valid:
            return False

        # Verify accessibility rule: each uploaded image requires an alt description
        files = [f for f in (self.gallery_files.data or []) if getattr(f, "filename", None)]
        alts = [line.strip() for line in (self.gallery_alts.data or "").splitlines() if line.strip()]

        if len(files) > 0:
            if len(alts) < len(files):
                self.gallery_alts.errors.append("Describe every image you upload.")
                return False

        return True

    def parse_tags(self):
        return parse_tag_string(self.tech_tags.data)
