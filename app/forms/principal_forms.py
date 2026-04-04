"""
PRINCIPAL FORMS
===============
WTForms classes for all Principal actions.
Validation rules are defined HERE — not in routes, not in services.
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField,
                     SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, Email, Length,
                                 EqualTo, Regexp, ValidationError)
from app.models.department import Department


class CreateDepartmentForm(FlaskForm):
    """Form for adding a new department."""

    name = StringField(
        'Department Name',
        validators=[
            DataRequired(message='Department name is required.'),
            Length(min=3, max=100,
                   message='Name must be between 3 and 100 characters.')
        ],
        render_kw={'placeholder': 'e.g. Computer Science and Engineering'}
    )

    code = StringField(
        'Short Code',
        validators=[
            DataRequired(message='Department code is required.'),
            Length(min=2, max=10, message='Code must be 2–10 characters.'),
            # Only letters and numbers allowed — no spaces or symbols
            Regexp(r'^[A-Za-z0-9]+$',
                   message='Code must contain only letters and numbers.')
        ],
        render_kw={'placeholder': 'e.g. CSE'}
    )

    program_type = SelectField(
        'Program Type',
        choices=[
            ('UG',   'UG — Under Graduate (B.Tech, B.Sc, B.Com)'),
            ('PG',   'PG — Post Graduate  (M.Tech, M.Sc, MBA)'),
            ('both', 'Both UG and PG'),
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField('Create Department')

    def validate_code(self, field):
        """
        Custom validator — WTForms calls any method named validate_<fieldname>
        automatically after the standard validators pass.
        """
        code = field.data.strip().upper()
        if Department.query.filter_by(code=code).first():
            raise ValidationError(
                f'Department code "{code}" is already taken. '
                f'Choose a different code.'
            )

    def validate_name(self, field):
        name = field.data.strip()
        if Department.query.filter_by(name=name).first():
            raise ValidationError(
                f'A department named "{name}" already exists.'
            )


class EditDepartmentForm(FlaskForm):
    """Same fields as Create, but used when editing — skips uniqueness
    check for the current department (handled in service layer)."""

    name = StringField(
        'Department Name',
        validators=[DataRequired(), Length(min=3, max=100)]
    )
    code = StringField(
        'Short Code',
        validators=[
            DataRequired(), Length(min=2, max=10),
            Regexp(r'^[A-Za-z0-9]+$', message='Letters and numbers only.')
        ]
    )
    program_type = SelectField(
        'Program Type',
        choices=[('UG', 'UG'), ('PG', 'PG'), ('both', 'Both UG and PG')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Save Changes')


class CreateHODForm(FlaskForm):
    """
    Form for creating a brand-new HOD account.
    Principal fills this in — a User + Teacher profile is created.
    """

    first_name = StringField(
        'First Name',
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={'placeholder': 'e.g. Dr. Ayesha'}
    )

    last_name = StringField(
        'Last Name',
        validators=[DataRequired(), Length(min=2, max=50)],
        render_kw={'placeholder': 'e.g. Khan'}
    )

    email = StringField(
        'Email Address',
        validators=[
            DataRequired(),
            Email(message='Enter a valid email address.')
        ],
        render_kw={'placeholder': 'hod@college.edu'}
    )

    employee_id = StringField(
        'Employee ID',
        validators=[
            DataRequired(),
            Length(min=3, max=20),
            Regexp(r'^[A-Za-z0-9]+$', message='Letters and numbers only.')
        ],
        render_kw={'placeholder': 'e.g. EMP2024001'}
    )

    department_id = SelectField(
        'Assign to Department',
        coerce=int,              # convert the string from HTML to int
        validators=[DataRequired(message='Please select a department.')]
    )

    password = PasswordField(
        'Temporary Password',
        validators=[
            DataRequired(),
            Length(min=8, message='Password must be at least 8 characters.')
        ],
        render_kw={'placeholder': 'Min. 8 characters'}
    )

    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match.')
        ]
    )

    submit = SubmitField('Create HOD Account')

    def __init__(self, *args, **kwargs):
        """
        Populate the department dropdown dynamically from the database.
        This runs every time the form is instantiated so new departments
        automatically appear without restarting the server.
        """
        super().__init__(*args, **kwargs)
        self.department_id.choices = [
            (d.id, f'{d.name} ({d.code})')
            for d in Department.query.filter_by(is_active=True)
                                     .order_by(Department.name).all()
        ]


class AssignHODForm(FlaskForm):
    """
    Form to reassign HOD role from one teacher to another
    within the same department.
    """

    department_id = SelectField(
        'Department',
        coerce=int,
        validators=[DataRequired()]
    )

    teacher_id = SelectField(
        'New HOD (select existing teacher)',
        coerce=int,
        validators=[DataRequired()]
    )

    submit = SubmitField('Assign as HOD')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.department_id.choices = [
            (d.id, f'{d.name} ({d.code})')
            for d in Department.query.filter_by(is_active=True)
                                     .order_by(Department.name).all()
        ]
        # Teacher choices loaded dynamically via JS when dept changes
        # Default: empty — JS will populate after dept selection
        self.teacher_id.choices = []