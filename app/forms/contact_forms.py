from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError


class ContactForm(FlaskForm):
    name = StringField("Your Name", validators=[DataRequired(message="Name is required."), Length(min=2, max=120)])
    email = StringField("Email Address", validators=[DataRequired(message="Email is required."), Email(message="Please enter a valid email address."), Length(max=255)])
    subject = StringField("Subject", validators=[Optional(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired(message="Message is required."), Length(min=10, max=4000, message="Message must be between 10 and 4000 characters.")])
    website = StringField("Website")  # Honeypot field
    submit = SubmitField("Send Message")

    def validate_website(self, field):
        if field.data and field.data.strip():
            raise ValidationError("Spam detected")
