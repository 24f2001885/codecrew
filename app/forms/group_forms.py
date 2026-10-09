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
        return parse_tag_string(self.tech_tags.data)
