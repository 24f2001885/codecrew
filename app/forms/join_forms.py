import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectMultipleField, SelectField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from app.services.alerts import normalize_tags


class JoinApplicationForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email Address", validators=[DataRequired(), Email(), Length(max=255)])
    project_types = SelectMultipleField(
        "Domains of Interest",
        choices=[
            ("web_app", "Web Application"),
            ("mobile_app", "Mobile App"),
            ("desktop_software", "Desktop Software"),
            ("api_backend", "API / Backend"),
            ("other", "Other"),
        ],
        validators=[DataRequired(message="Please select at least one domain of interest.")],
    )
    domain_tags = StringField(
        "Specialized Skills / Domain Tags",
        description="Comma-separated skills (e.g. react, postgres, fintech)",
        validators=[Optional(), Length(max=500)],
    )
    headline = StringField(
        "Professional Headline",
        description="e.g. Senior Fullstack Developer (Python / Vue)",
        validators=[Optional(), Length(max=160)],
    )
    portfolio_url = StringField("Portfolio or GitHub URL", validators=[Optional(), Length(max=255)])
    message = TextAreaField("Intro / Message", validators=[Optional(), Length(max=2000)])
    resume_pdf = FileField(
        "Resume (PDF only, max 5MB)",
        validators=[
            Optional(),
            FileAllowed(["pdf"], "Only PDF files are permitted for resumes."),
        ],
    )
    alerts_consent = BooleanField(
        "Email me about projects in my domains; I can unsubscribe at any time.",
        validators=[DataRequired(message="You must consent to receive domain project alerts.")],
    )
    honeypot = HiddenField()

    def validate_domain_tags(self, field):
        if not field.data:
            return
        tags = [t.strip() for t in field.data.split(",") if t.strip()]
        if len(tags) > 20:
            raise ValidationError("You may specify at most 20 tags.")
        for t in tags:
            if len(t) > 30:
                raise ValidationError(f"Tag '{t}' is too long (maximum 30 characters per tag).")

    def validate_resume_pdf(self, field):
        if field.data and getattr(field.data, "filename", None):
            # Check file size (5MB max)
            field.data.seek(0, 2)
            size = field.data.tell()
            field.data.seek(0)
            if size > 5 * 1024 * 1024:
                raise ValidationError("Resume file exceeds maximum allowed size of 5 MB.")

            # Validate %PDF- header magic bytes
            header = field.data.read(5)
            field.data.seek(0)
            if header != b"%PDF-":
                raise ValidationError("Uploaded file is not a valid PDF document.")

    def parse_tags(self):
        return normalize_tags(self.domain_tags.data or "")


class AdminConvertApplicationForm(FlaskForm):
    group_id = SelectField("Assign to Group", validators=[DataRequired()])
    member_name = StringField("Member Name", validators=[DataRequired(), Length(max=120)])
    role = StringField("Role in Group", validators=[Optional(), Length(max=120)])
    username = StringField("Coder Username", validators=[DataRequired(), Length(min=3, max=80)])


class AdminAlertNotifyForm(FlaskForm):
    summary = TextAreaField(
        "Anonymized Project Summary",
        validators=[DataRequired(), Length(max=600)],
        description="Max 600 characters. Never include client names, email, budget, or private specifics.",
    )
