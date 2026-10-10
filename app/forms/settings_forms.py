from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    IntegerField,
    BooleanField,
    FileField,
    MultipleFileField,
    URLField,
    SubmitField,
)
from wtforms.validators import Optional, Length, URL, NumberRange


class SettingsForm(FlaskForm):
    # Hero Section
    hero_headline = StringField("Hero Headline", validators=[Optional(), Length(max=200)])
    hero_subheadline = TextAreaField("Hero Subheadline", validators=[Optional(), Length(max=300)])
    hero_cta_text = StringField("Hero CTA Text", validators=[Optional(), Length(max=80)])
    hero_images = MultipleFileField("Hero Images", validators=[Optional()])
    hero_image_alts = TextAreaField("Hero Image Descriptions (one per line)", validators=[Optional()])

    # Footer & Social Links
    github_url = URLField("GitHub URL", validators=[Optional(), URL(message="Invalid URL format.")])
    twitter_url = URLField("Twitter URL", validators=[Optional(), URL(message="Invalid URL format.")])
    linkedin_url = URLField("LinkedIn URL", validators=[Optional(), URL(message="Invalid URL format.")])
    instagram_url = URLField("Instagram URL", validators=[Optional(), URL(message="Invalid URL format.")])

    # SEO Defaults
    seo_default_title = StringField("Default SEO Title", validators=[Optional(), Length(max=200)])
    seo_default_description = TextAreaField("Default Meta Description", validators=[Optional(), Length(max=300)])
    seo_default_og_image = FileField("Default OG Image", validators=[Optional()])

    # Stats Override
    override_stats = BooleanField("Override Platform Stats")
    stats_groups = IntegerField("Groups Count", validators=[Optional(), NumberRange(min=0, message="Must be non-negative.")])
    stats_members = IntegerField("Members Count", validators=[Optional(), NumberRange(min=0, message="Must be non-negative.")])
    stats_projects = IntegerField("Projects Count", validators=[Optional(), NumberRange(min=0, message="Must be non-negative.")])

    coder_applications_open = BooleanField("Accept Coder Applications", default=True)
    auto_send_domain_alerts = BooleanField("Auto-Send Domain Alerts on New Requests", default=False)
    submit = SubmitField("Save Settings")

    def validate(self, extra_validators=None):
        initial_valid = super().validate(extra_validators=extra_validators)
        if not initial_valid:
            return False

        # 1. When override_stats is checked, all three numbers are required
        if self.override_stats.data:
            has_error = False
            if self.stats_groups.data is None:
                self.stats_groups.errors.append("Groups count is required when override is enabled.")
                has_error = True
            if self.stats_members.data is None:
                self.stats_members.errors.append("Members count is required when override is enabled.")
                has_error = True
            if self.stats_projects.data is None:
                self.stats_projects.errors.append("Projects count is required when override is enabled.")
                has_error = True
            if has_error:
                return False

        # 2. Hero images require alt descriptions
        files = [f for f in (self.hero_images.data or []) if getattr(f, "filename", None)]
        alts = [line.strip() for line in (self.hero_image_alts.data or "").splitlines() if line.strip()]
        if len(files) > 0 and len(alts) < len(files):
            self.hero_image_alts.errors.append("Describe every hero image you upload.")
            return False

        return True
