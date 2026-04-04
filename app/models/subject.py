from app import db
from app.models.teacher import teacher_subjects
from datetime import datetime


class Subject(db.Model):
    """
    A subject (course) belongs to one department and is taught in
    a specific semester.

    Examples:
      - Data Structures  → CSE dept, Semester 3, UG
      - Machine Learning → CSE dept, Semester 5, UG
      - Advanced VLSI    → ECE dept, Semester 2, PG

    One Subject → many Attendance records
    One Subject ← many Teachers (via teacher_subjects association table)
    """
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)

    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'),
                              nullable=False)

    # Subject name e.g. "Data Structures and Algorithms"
    name = db.Column(db.String(100), nullable=False)

    # Short code used in timetables and reports e.g. "DSA", "ML", "OS"
    code = db.Column(db.String(15), unique=True, nullable=False)

    # ------------------------------------------------------------------ #
    #  WHICH SEMESTER this subject is taught in.
    #  Combined with program_type, this tells us exactly which students
    #  are enrolled in this subject.
    #  e.g. semester=3 + program_type='UG' → all UG 3rd semester students
    # ------------------------------------------------------------------ #
    semester     = db.Column(db.Integer, nullable=False)
    program_type = db.Column(db.String(5), nullable=False, default='UG')

    # Total number of classes planned for this subject this semester.
    # Used to calculate attendance percentage:
    #   attendance% = (classes_attended / total_classes) × 100
    total_classes = db.Column(db.Integer, default=0, nullable=False)

    is_active  = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ------------------------------------------------------------------ #
    #  RELATIONSHIPS
    # ------------------------------------------------------------------ #
    department = db.relationship('Department', back_populates='subjects')

    # Many-to-many back-reference to Teacher
    # back_populates='subjects' links to Teacher.subjects
    teachers   = db.relationship('Teacher', secondary=teacher_subjects,
                                 back_populates='subjects', lazy='dynamic')

    # All attendance records for this subject
    attendance_records = db.relationship('Attendance', back_populates='subject',
                                         lazy='dynamic',
                                         cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Subject {self.code} - Sem {self.semester} [{self.program_type}]>'