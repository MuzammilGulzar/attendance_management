from app import db
from datetime import datetime


class Department(db.Model):
    """
    A department is the top-level organisational unit.
    Examples: Computer Science, Electronics, MBA.

    One Department  →  many Teachers
    One Department  →  many Students
    One Department  →  one HOD (stored via Teacher.is_hod flag)
    One Department  →  many Subjects
    """
    __tablename__ = 'departments'

    id   = db.Column(db.Integer, primary_key=True)

    # Department full name e.g. "Computer Science and Engineering"
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Short code e.g. "CSE", "ECE", "MBA" — used in reports and displays
    code = db.Column(db.String(10),  unique=True, nullable=False)

    # ------------------------------------------------------------------ #
    #  PROGRAM TYPE
    #  A department can offer UG, PG, or both.
    #  'both' means the department has both B.Tech and M.Tech students.
    # ------------------------------------------------------------------ #
    program_type = db.Column(
        db.String(10),
        nullable=False,
        default='UG'
        # Valid values: 'UG', 'PG', 'both'
    )

    is_active  = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ------------------------------------------------------------------ #
    #  RELATIONSHIPS
    #  back_populates='department' means the other model also has a
    #  relationship pointing back here — they are linked to each other.
    #  lazy='dynamic' means the query is not run until you call .all()
    #  This is memory-efficient for large collections.
    # ------------------------------------------------------------------ #
    teachers = db.relationship('Teacher', back_populates='department',
                               lazy='dynamic')
    students = db.relationship('Student', back_populates='department',
                               lazy='dynamic')
    subjects = db.relationship('Subject', back_populates='department',
                               lazy='dynamic')

    @property
    def hod(self):
        """
        Returns the current HOD Teacher for this department.
        Usage:  department.hod.user.full_name
        """
        return self.teachers.filter_by(is_hod=True, is_active=True).first()

    @property
    def total_students(self):
        return self.students.filter_by(is_graduated=False).count()

    def __repr__(self):
        return f'<Department {self.code} - {self.name}>'