from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message="Username is required.")])
    password = PasswordField("Password", validators=[DataRequired(message="Password is required.")])
    submit = SubmitField("Log In")


class ForgotPasswordForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message="Username is required.")])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=10, message="Password must be at least 10 characters long."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Reset Password")
