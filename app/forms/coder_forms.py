from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    PasswordField,
    SelectField,
    FileField,
    MultipleFileField,
    URLField,
    DateTimeField,
    SubmitField,
)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, URL
from app.forms import parse_tag_string


class CoderAdminForm(FlaskForm):
    member_id = SelectField("Team Member", coerce=str, validators=[DataRequired(message="Select a team member.")])
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    submit = SubmitField("Invite Coder")


class CoderEditForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    submit = SubmitField("Update Coder")


class CoderInviteAcceptForm(FlaskForm):
    password = PasswordField("New Password", validators=[
        DataRequired(),
        Length(min=10, message="Password must be at least 10 characters long."),
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo("password", message="Passwords must match."),
    ])
    submit = SubmitField("Activate Account")


class CoderLoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message="Username is required.")])
    password = PasswordField("Password", validators=[DataRequired(message="Password is required.")])
    submit = SubmitField("Log In")


class CoderForgotPasswordForm(FlaskForm):
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    submit = SubmitField("Send Reset Link")


class CoderResetPasswordForm(FlaskForm):
    password = PasswordField("New Password", validators=[
        DataRequired(),
        Length(min=10, message="Password must be at least 10 characters long."),
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo("password", message="Passwords must match."),
    ])
    submit = SubmitField("Reset Password")


class CoderProfileForm(FlaskForm):
    role = StringField("Role / Title", validators=[Optional(), Length(max=100)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=500)])
    skill_tags = StringField("Skills (comma separated)", validators=[Optional()])
    github_url = URLField("GitHub URL", validators=[Optional(), URL(message="Invalid URL format.")])
    linkedin_url = URLField("LinkedIn URL", validators=[Optional(), URL(message="Invalid URL format.")])
    twitter_url = URLField("Twitter URL", validators=[Optional(), URL(message="Invalid URL format.")])
    photo = FileField("Profile Photo", validators=[Optional()])
    resume_pdf = FileField("Resume (PDF)", validators=[Optional()])
    submit = SubmitField("Save Profile")

    def parse_tags(self):
        return parse_tag_string(self.skill_tags.data)


class CoderProjectForm(FlaskForm):
    title = StringField("Project Title", validators=[DataRequired(message="Title is required."), Length(min=2, max=150)])
    summary = TextAreaField("Summary", validators=[Optional(), Length(max=300)])
    description = TextAreaField("Description", validators=[Optional()])
    tech_tags = StringField("Tech Stack (comma separated)", validators=[Optional()])
    demo_url = URLField("Demo URL", validators=[Optional(), URL(message="Invalid URL format.")])
    live_url = URLField("Live URL", validators=[Optional(), URL(message="Invalid URL format.")])
    github_url = URLField("GitHub URL", validators=[Optional(), URL(message="Invalid URL format.")])
    screenshot = FileField("Cover Screenshot", validators=[Optional()])
    gallery_images = MultipleFileField("Gallery Images", validators=[Optional()])
    gallery_alts = TextAreaField("Gallery Image Alt Descriptions (one per line)", validators=[Optional()])
    submit = SubmitField("Save Project")

    def parse_tags(self):
        return parse_tag_string(self.tech_tags.data)

    def validate(self, extra_validators=None):
        initial_valid = super().validate(extra_validators=extra_validators)
        if not initial_valid:
            return False

        files = [f for f in (self.gallery_images.data or []) if getattr(f, "filename", None)]
        alts = [line.strip() for line in (self.gallery_alts.data or "").splitlines() if line.strip()]
        if len(files) > 0 and len(alts) < len(files):
            self.gallery_alts.errors.append("Describe every gallery image you upload.")
            return False
        return True


class GrantAccessForm(FlaskForm):
    coder_id = SelectField("Select Coder", coerce=str, validators=[DataRequired(message="Select a coder.")])
    scope = SelectField("Access Scope", choices=[
        ("brief_only", "Brief Only (Requester name and email hidden)"),
        ("brief_and_contact", "Brief & Contact Details (Reveals requester identity)"),
    ], default="brief_only", validators=[DataRequired()])
    expires_at = DateTimeField("Expiration (Optional, UTC: YYYY-MM-DD HH:MM)", format="%Y-%m-%d %H:%M", validators=[Optional()])
    submit = SubmitField("Grant Access")
