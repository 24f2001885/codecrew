from pathlib import Path
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, FileField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, URL, ValidationError
from app.forms import parse_tag_string


class MemberForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(message="Member name is required."), Length(min=2, max=120)])
    role = StringField("Role / Title", validators=[Optional(), Length(max=120)])
    bio = TextAreaField("Biography", validators=[Optional()])
    skill_tags = StringField("Skills (comma separated)", validators=[Optional()])
    github_url = URLField("GitHub URL", validators=[Optional(), URL(message="Invalid URL format.")])
    linkedin_url = URLField("LinkedIn URL", validators=[Optional(), URL(message="Invalid URL format.")])
    twitter_url = URLField("Twitter / X URL", validators=[Optional(), URL(message="Invalid URL format.")])
    display_order = IntegerField("Display Order", default=0, validators=[NumberRange(min=0, message="Display order must be 0 or greater.")])
    photo = FileField("Profile Photo", validators=[Optional()])
    resume_pdf = FileField("Resume / CV (PDF only)", validators=[Optional()])
    remove_photo = BooleanField("Remove current photo")
    remove_resume = BooleanField("Remove current resume")
    submit = SubmitField("Save Member")

    def validate_resume_pdf(self, field):
        if field.data and hasattr(field.data, "filename") and field.data.filename:
            ext = Path(field.data.filename).suffix.lower()
            if ext != ".pdf":
                raise ValidationError("Only PDF files (.pdf) are allowed for resumes.")

    def parse_tags(self):
        return parse_tag_string(self.skill_tags.data)
