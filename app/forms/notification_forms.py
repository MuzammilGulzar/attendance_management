"""
NOTIFICATION FORMS
==================
"""
from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField,
                     IntegerField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional


class SendNotificationForm(FlaskForm):
    """
    Universal send form — target_type drives which secondary fields appear.
    JS in the template shows/hides the appropriate secondary field.
    """

    # What kind of target?
    target_type = SelectField(
        'Send To',
        choices=[
            ('single_student', 'One Student'),
            ('single_teacher', 'One Teacher'),
            ('semester',       'All Students in a Semester'),
            ('all_students',   'All Students in Department'),
            ('all_teachers',   'All Teachers in Department'),
        ],
        validators=[DataRequired()]
    )

    # Populated dynamically via JS + AJAX for single targets
    recipient_user_id = SelectField(
        'Select Recipient',
        coerce=int,
        validators=[Optional()],
        choices=[]
    )

    # For semester broadcast
    semester = SelectField(
        'Semester',
        coerce=int,
        validators=[Optional()],
        choices=[(i, f'Semester {i}') for i in range(1, 9)]
    )

    program_type = SelectField(
        'Program Type',
        validators=[Optional()],
        choices=[('UG', 'UG — Under Graduate'), ('PG', 'PG — Post Graduate')]
    )

    # Notification content
    notif_type = SelectField(
        'Message Type',
        choices=[
            ('info',    'Info (Blue)'),
            ('warning', 'Warning (Amber)'),
            ('success', 'Success (Green)'),
            ('danger',  'Urgent (Red)'),
        ],
        validators=[DataRequired()],
        default='info'
    )

    title = StringField(
        'Subject / Title',
        validators=[DataRequired(), Length(min=3, max=100)],
        render_kw={'placeholder': 'e.g. Reminder: Lab submission due tomorrow'}
    )

    message = TextAreaField(
        'Message',
        validators=[DataRequired(), Length(min=10, max=1000)],
        render_kw={
            'rows'       : 4,
            'placeholder': 'Write your message here...'
        }
    )

    submit = SubmitField('Send Notification')
