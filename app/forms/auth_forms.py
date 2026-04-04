"""
AUTH FORMS
==========
WTForms defines form fields and validation rules as Python classes.
Flask-WTF adds:
  - CSRF token automatically (hidden field, stops cross-site attacks)
  - Integration with Flask's request context

When a form is submitted, calling form.validate_on_submit() runs
ALL validators automatically — no if/else chains needed in the route.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    """
    Fields:
      email      → must be a valid email format
      password   → required, no length check at login (we check the hash)
      remember   → checkbox — if checked, session persists after browser close
    """
    email = StringField(
        'Email Address',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.')
        ]
    )

    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.')
        ]
    )

    # "Remember me" — Flask-Login uses this to set a long-lived cookie
    remember = BooleanField('Remember Me')

    submit = SubmitField('Log In')


class ChangePasswordForm(FlaskForm):
    """
    Used by any logged-in user to change their own password.
    EqualTo validator ensures new_password == confirm_password.
    """
    current_password = PasswordField(
        'Current Password',
        validators=[DataRequired()]
    )

    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters.')
        ]
    )

    confirm_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(),
            EqualTo('new_password', message='Passwords must match.')
        ]
    )

    submit = SubmitField('Change Password')