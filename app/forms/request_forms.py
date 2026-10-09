from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError

PROJECT_TYPES = [
    ("web_app", "Web App"),
    ("mobile_app", "Mobile App"),
    ("desktop_software", "Desktop Software"),
    ("api_backend", "API / Backend"),
    ("other", "Other"),
]


class RequestForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(message="Name is required."), Length(min=2, max=120)])
    email = StringField("Email Address", validators=[DataRequired(message="Email is required."), Email(message="Please enter a valid email address.")])
    company = StringField("Company / Organization", validators=[Optional(), Length(max=150)])
    project_type = SelectField(
        "Project Type",
        choices=PROJECT_TYPES,
        validators=[DataRequired(message="Please select a project type.")],
    )
    budget_range = StringField("Estimated Budget Range", validators=[Optional(), Length(max=80)])
    timeline = StringField("Desired Timeline", validators=[Optional(), Length(max=80)])
    description = TextAreaField(
        "Project Description",
        validators=[DataRequired(message="Description is required."), Length(min=20, max=5000, message="Description must be between 20 and 5000 characters.")],
    )
    attachment = FileField(
        "Project Brief / Specifications (Optional)",
        validators=[Optional(), FileAllowed(["pdf", "docx"], "Only PDF and DOCX documents are supported.")],
    )
    website = StringField("Website")  # Honeypot field
    submit = SubmitField("Submit Project Request")

    def validate_website(self, field):
        if field.data and field.data.strip():
            raise ValidationError("Spam detected")
