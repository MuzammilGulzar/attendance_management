"""
HOD FORMS
=========
WTForms for all HOD dashboard actions.
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField,
                     IntegerField, SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, Email, Length,
                                 EqualTo, NumberRange, Regexp, Optional)


class CreateTeacherForm(FlaskForm):
    first_name  = StringField('First Name',
                    validators=[DataRequired(), Length(min=2, max=50)])
    last_name   = StringField('Last Name',
                    validators=[DataRequired(), Length(min=2, max=50)])
    email       = StringField('Email',
                    validators=[DataRequired(), Email()])
    employee_id = StringField('Employee ID',
                    validators=[DataRequired(), Length(min=3, max=20),
                                Regexp(r'^[A-Za-z0-9]+$',
                                       message='Letters and numbers only.')])
    password    = PasswordField('Password',
                    validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                    validators=[DataRequired(),
                                EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Create Teacher')


class EditTeacherForm(FlaskForm):
    first_name  = StringField('First Name',
                    validators=[DataRequired(), Length(min=2, max=50)])
    last_name   = StringField('Last Name',
                    validators=[DataRequired(), Length(min=2, max=50)])
    employee_id = StringField('Employee ID',
                    validators=[DataRequired(), Length(min=3, max=20),
                                Regexp(r'^[A-Za-z0-9]+$',
                                       message='Letters and numbers only.')])
    submit = SubmitField('Save Changes')


class AssignSubjectForm(FlaskForm):
    """Assign/unassign a subject to a teacher."""
    teacher_id = SelectField('Teacher', coerce=int,
                              validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int,
                              validators=[DataRequired()])
    submit = SubmitField('Assign Subject')

    def __init__(self, dept_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if dept_id:
            from app.models.teacher import Teacher
            from app.models.subject import Subject
            self.teacher_id.choices = [
                (t.id, f'{t.full_name} ({t.employee_id})')
                for t in Teacher.query.filter_by(
                    department_id=dept_id, is_active=True, is_hod=False
                ).all()
            ]
            self.subject_id.choices = [
                (s.id, f'{s.name} ({s.code}) — Sem {s.semester}')
                for s in Subject.query.filter_by(
                    department_id=dept_id, is_active=True
                ).order_by(Subject.semester).all()
            ]


class CreateSubjectForm(FlaskForm):
    name = StringField('Subject Name',
                validators=[DataRequired(), Length(min=2, max=100)])
    code = StringField('Subject Code',
                validators=[DataRequired(), Length(min=2, max=15),
                            Regexp(r'^[A-Za-z0-9]+$',
                                   message='Letters and numbers only.')])
    semester = SelectField('Semester', coerce=int,
                validators=[DataRequired()],
                choices=[(i, f'Semester {i}') for i in range(1, 9)])
    program_type = SelectField('Program Type',
                validators=[DataRequired()],
                choices=[('UG', 'UG — Under Graduate'),
                         ('PG', 'PG — Post Graduate')])
    total_classes = IntegerField('Total Classes Planned',
                validators=[DataRequired(),
                            NumberRange(min=1, max=200,
                                        message='Must be between 1 and 200.')])
    submit = SubmitField('Create Subject')


class EditSubjectForm(FlaskForm):
    name = StringField('Subject Name',
                validators=[DataRequired(), Length(min=2, max=100)])
    code = StringField('Subject Code',
                validators=[DataRequired(), Length(min=2, max=15),
                            Regexp(r'^[A-Za-z0-9]+$',
                                   message='Letters and numbers only.')])
    semester = SelectField('Semester', coerce=int,
                validators=[DataRequired()],
                choices=[(i, f'Semester {i}') for i in range(1, 9)])
    program_type = SelectField('Program Type',
                validators=[DataRequired()],
                choices=[('UG', 'UG'), ('PG', 'PG')])
    total_classes = IntegerField('Total Classes Planned',
                validators=[DataRequired(),
                            NumberRange(min=1, max=200)])
    submit = SubmitField('Save Changes')


class CreateStudentForm(FlaskForm):
    first_name     = StringField('First Name',
                        validators=[DataRequired(), Length(min=2, max=50)])
    last_name      = StringField('Last Name',
                        validators=[DataRequired(), Length(min=2, max=50)])
    email          = StringField('Email',
                        validators=[DataRequired(), Email()])
    roll_number    = StringField('Roll Number',
                        validators=[DataRequired(), Length(min=3, max=20)])
    admission_year = StringField('Admission Year',
                        validators=[DataRequired(), Length(min=4, max=9)],
                        render_kw={'placeholder': '2024-25'})
    program_type   = SelectField('Program Type',
                        validators=[DataRequired()],
                        choices=[('UG', 'UG — Under Graduate'),
                                 ('PG', 'PG — Post Graduate')])
    semester       = SelectField('Starting Semester', coerce=int,
                        validators=[DataRequired()],
                        choices=[(i, f'Semester {i}') for i in range(1, 9)])
    password       = PasswordField('Temporary Password',
                        validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                        validators=[DataRequired(),
                                    EqualTo('password',
                                            message='Passwords must match.')])
    submit = SubmitField('Enroll Student')


class DeleteStudentForm(FlaskForm):
    """
    Reason is MANDATORY for student deletion.
    This creates an audit trail — you always know WHY a student was removed.
    """
    reason = TextAreaField('Reason for Removal',
                validators=[DataRequired(),
                            Length(min=5, max=500,
                                   message='Reason must be 5–500 characters.')],
                render_kw={'rows': 3,
                           'placeholder': 'e.g. Student transferred to another institution'})
    submit = SubmitField('Confirm Removal')


class BulkPromoteForm(FlaskForm):
    """
    HOD selects: which semester to promote FROM, and which program type.
    The system promotes ALL eligible students at that semester.
    """
    program_type = SelectField('Program Type',
                    validators=[DataRequired()],
                    choices=[('UG', 'UG — Under Graduate'),
                             ('PG', 'PG — Post Graduate')])
    from_semester = SelectField('Promote FROM Semester', coerce=int,
                    validators=[DataRequired()],
                    choices=[(i, f'Semester {i} → Semester {i+1}')
                             for i in range(1, 8)])
    submit = SubmitField('Promote All Eligible Students')