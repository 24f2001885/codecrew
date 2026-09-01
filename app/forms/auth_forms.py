"""
FILE PURPOSE: Flask-WTF forms for the admin auth flow (PDR §5.2, TDR §5).

PROMPT FOR LLM IMPLEMENTATION:
1. Import FlaskForm from flask_wtf, StringField/PasswordField/
   SubmitField from wtforms, DataRequired/Length/EqualTo from
   wtforms.validators.
2. class LoginForm(FlaskForm): username = StringField("Username",
   validators=[DataRequired()]); password = PasswordField("Password",
   validators=[DataRequired()]); submit = SubmitField("Log In").
3. class ForgotPasswordForm(FlaskForm): username = StringField(
   "Username", validators=[DataRequired()]); submit = SubmitField(
   "Send Reset Link") — matches forgot_password.html's single field
   (target email comes from config, not the form, per TDR §16).
4. class ResetPasswordForm(FlaskForm): password = PasswordField(
   "New Password", validators=[DataRequired(), Length(min=8)]);
   confirm_password = PasswordField("Confirm Password", validators=
   [DataRequired(), EqualTo("password", message="Passwords must
   match.")]); submit = SubmitField("Reset Password").
5. CSRF protection is automatic via FlaskForm + the global CSRFProtect()
   in app/extensions.py — no per-form CSRF code needed (TDR §6).

DEBUGGING:
# print("[DEBUG] auth_forms.py — LoginForm/ForgotPasswordForm/ResetPasswordForm defined")

OFFLINE DOCKER TEST CASES:
- LoginForm(username="", password="x").validate() is False (username
  required).
- ResetPasswordForm(password="longenough1", confirm_password=
  "different").validate() is False (EqualTo mismatch).
- ResetPasswordForm(password="short", confirm_password="short")
  .validate() is False (Length(min=8) rejects it).
"""
