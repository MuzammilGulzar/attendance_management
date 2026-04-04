"""
GRADUATION FORMS
================
Forms specifically for the graduation workflow.
"""

from flask_wtf import FlaskForm
from wtforms import (TextAreaField, SelectField, SubmitField)
from wtforms.validators import DataRequired, Length


class GraduateStudentForm(FlaskForm):
    """
    Single-student graduation form.

    The reason field is mandatory and has a minimum length — this
    becomes a permanent part of the student's academic record.
    A one-word reason like "done" is not acceptable.
    """
    reason = TextAreaField(
        'Graduation Note / Reason',
        validators=[
            DataRequired(message='A graduation reason is required.'),
            Length(
                min=10,
                max=500,
                message='Reason must be between 10 and 500 characters. '
                        'This is a permanent academic record.'
            )
        ],
        render_kw={
            'rows'        : 3,
            'placeholder' : (
                'e.g. Completed all 8 semesters of B.Tech programme '
                'with satisfactory attendance and results.'
            )
        }
    )
    submit = SubmitField('Confirm Graduation')


class BulkGraduateForm(FlaskForm):
    """
    Bulk graduation form — graduates an entire batch at once.
    HOD selects program_type + graduation semester.
    """
    program_type = SelectField(
        'Programme',
        choices=[('UG', 'UG — Under Graduate'), ('PG', 'PG — Post Graduate')],
        validators=[DataRequired()]
    )

    semester = SelectField(
        'Graduation Semester',
        coerce=int,
        validators=[DataRequired()],
        # Choices shown depend on program_type — JS updates them dynamically
        choices=[
            (6, 'Semester 6 (UG early exit)'),
            (8, 'Semester 8 (UG full programme)'),
            (4, 'Semester 4 (PG full programme)'),
        ]
    )

    reason = TextAreaField(
        'Batch Graduation Note',
        validators=[
            DataRequired(),
            Length(min=10, max=500,
                   message='Reason must be at least 10 characters.')
        ],
        render_kw={
            'rows'       : 3,
            'placeholder': 'e.g. End of academic year 2024–25. '
                           'All students completed programme requirements.'
        }
    )

    submit = SubmitField('Graduate Entire Batch')
