from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.forms import parse_tag_string


class BlogPostForm(FlaskForm):
    group_id = SelectField("Group", validators=[DataRequired(message="Group is required.")])
    title = StringField("Title", validators=[DataRequired(message="Title is required."), Length(min=3, max=200)])
    content = TextAreaField("Content", validators=[DataRequired(message="Content is required."), Length(min=20)])
    tags = StringField("Tags (comma separated)", validators=[Optional()])
    cover_image = FileField(
        "Cover Image",
        validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp", "gif"], "Images only!")]
    )
    published = BooleanField("Publish now")
    submit = SubmitField("Save Post")

    def validate_tags(self, field):
        if field.data:
            parse_tag_string(field.data)

    def parse_tags(self):
        return parse_tag_string(self.tags.data)
