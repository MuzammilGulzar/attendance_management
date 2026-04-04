# from app import db
# from datetime import datetime


# # Association table — links Teachers to the Subjects they teach.
# # This is a MANY-TO-MANY relationship:
# #   One Teacher can teach many Subjects
# #   One Subject can be taught by many Teachers
# # We use a plain association table (no extra columns needed).
# teacher_subjects = db.Table(
#     'teacher_subjects',
#     db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'),
#               primary_key=True),
#     db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id'),
#               primary_key=True)
# )


# class Teacher(db.Model):
#     """
#     Teacher profile — linked 1-to-1 with a User account.

#     Separation of concerns:
#       User table  → login credentials (email, password, role)
#       Teacher table → professional details (department, employee ID)

#     This way the login system stays clean and role-specific data
#     lives in its own table.
#     """
#     __tablename__ = 'teachers'

#     id = db.Column(db.Integer, primary_key=True)

#     # ------------------------------------------------------------------ #
#     #  FOREIGN KEY to users table
#     #  db.ForeignKey('users.id') means: this column must contain a value
#     #  that exists in the 'id' column of the 'users' table.
#     #  unique=True enforces the 1-to-1 relationship (one user = one teacher)
#     # ------------------------------------------------------------------ #
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
#                         unique=True, nullable=False)

#     # ------------------------------------------------------------------ #
#     #  FOREIGN KEY to departments table
#     # ------------------------------------------------------------------ #
#     department_id = db.Column(db.Integer, db.ForeignKey('departments.id'),
#                               nullable=False)

#     # Official employee/staff ID issued by the college
#     employee_id = db.Column(db.String(20), unique=True, nullable=False)

#     # ------------------------------------------------------------------ #
#     #  HOD FLAG
#     #  Instead of creating a separate HOD table, we mark a teacher as HOD.
#     #  Only ONE teacher per department should have is_hod=True at any time.
#     #  This is enforced in the service layer (not at DB level).
#     # ------------------------------------------------------------------ #
#     is_hod = db.Column(db.Boolean, default=False, nullable=False)

#     is_active  = db.Column(db.Boolean, default=True, nullable=False)
#     joined_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow,
#                            onupdate=datetime.utcnow, nullable=False)

#     # ------------------------------------------------------------------ #
#     #  RELATIONSHIPS
#     # ------------------------------------------------------------------ #
#     # Back to the User who owns this profile
#     user       = db.relationship('User', back_populates='teacher_profile')

#     # Which department this teacher belongs to
#     department = db.relationship('Department', back_populates='teachers')

#     # Many-to-many: subjects this teacher teaches
#     # secondary=teacher_subjects → use the association table defined above
#     subjects   = db.relationship('Subject', secondary=teacher_subjects,
#                                  back_populates='teachers', lazy='dynamic')

#     # All attendance records marked BY this teacher
#     attendance_records = db.relationship('Attendance', foreign_keys='Attendance.marked_by_id', back_populates='marked_by',
#                                          lazy='dynamic')

#     @property
#     def full_name(self):
#         return self.user.full_name if self.user else 'Unknown'

#     @property
#     def email(self):
#         return self.user.email if self.user else ''

#     def __repr__(self):
#         return f'<Teacher {self.employee_id} - {self.full_name}>'

#########3-----------updated------------
from app import db
from datetime import datetime


# Association table — links Teachers to the Subjects they teach.
# This is a MANY-TO-MANY relationship:
#   One Teacher can teach many Subjects
#   One Subject can be taught by many Teachers
# We use a plain association table (no extra columns needed).
teacher_subjects = db.Table(
    'teacher_subjects',
    db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id'),
              primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id'),
              primary_key=True)
)


class Teacher(db.Model):
    """
    Teacher profile — linked 1-to-1 with a User account.

    Separation of concerns:
      User table  → login credentials (email, password, role)
      Teacher table → professional details (department, employee ID)

    This way the login system stays clean and role-specific data
    lives in its own table.
    """
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)

    # ------------------------------------------------------------------ #
    #  FOREIGN KEY to users table
    #  db.ForeignKey('users.id') means: this column must contain a value
    #  that exists in the 'id' column of the 'users' table.
    #  unique=True enforces the 1-to-1 relationship (one user = one teacher)
    # ------------------------------------------------------------------ #
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        unique=True, nullable=False)

    # ------------------------------------------------------------------ #
    #  FOREIGN KEY to departments table
    # ------------------------------------------------------------------ #
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'),
                              nullable=False)

    # Official employee/staff ID issued by the college
    employee_id = db.Column(db.String(20), unique=True, nullable=False)

    # ------------------------------------------------------------------ #
    #  HOD FLAG
    #  Instead of creating a separate HOD table, we mark a teacher as HOD.
    #  Only ONE teacher per department should have is_hod=True at any time.
    #  This is enforced in the service layer (not at DB level).
    # ------------------------------------------------------------------ #
    is_hod = db.Column(db.Boolean, default=False, nullable=False)

    is_active  = db.Column(db.Boolean, default=True, nullable=False)
    joined_at  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # ------------------------------------------------------------------ #
    #  RELATIONSHIPS
    # ------------------------------------------------------------------ #
    # Back to the User who owns this profile
    user       = db.relationship('User', back_populates='teacher_profile')

    # Which department this teacher belongs to
    department = db.relationship('Department', back_populates='teachers')

    # Many-to-many: subjects this teacher teaches
    # secondary=teacher_subjects → use the association table defined above
    subjects   = db.relationship('Subject', secondary=teacher_subjects,
                                 back_populates='teachers', lazy='dynamic')

    # All attendance records marked BY this teacher
    attendance_records = db.relationship('Attendance', foreign_keys='Attendance.marked_by_id', back_populates='marked_by',
                                         lazy='dynamic')

    @property
    def full_name(self):
        return self.user.full_name if self.user else 'Unknown'

    @property
    def email(self):
        return self.user.email if self.user else ''

    def __repr__(self):
        return f'<Teacher {self.employee_id} - {self.full_name}>'
