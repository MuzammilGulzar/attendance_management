# from app import db
# from datetime import datetime


# class Student(db.Model):
#     """
#     Student profile — linked 1-to-1 with a User account.

#     KEY DESIGN DECISIONS:
#     ─────────────────────
#     1. program_type (UG/PG) determines the graduation semester ceiling.
#        UG can graduate at semester 6 OR 8 (honours/lateral entry).
#        PG graduates at semester 4.

#     2. semester is the CURRENT semester the student is in.
#        It is manually promoted by the HOD — the system never auto-promotes.

#     3. is_graduated=True makes the student inactive. They can no longer
#        be promoted, and their User.is_active is set to False so they
#        cannot log in. BUT their data is permanently preserved.

#     4. graduation_semester records WHICH semester they graduated from.
#        This is important for transcripts and historical records.

#     5. graduation_reason is a free-text note the HOD writes when
#        graduating a student (e.g. "Completed 8 semesters with honours").
#     """
#     __tablename__ = 'students'

#     id = db.Column(db.Integer, primary_key=True)

#     # ------------------------------------------------------------------ #
#     #  FOREIGN KEYS
#     # ------------------------------------------------------------------ #
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
#                         unique=True, nullable=False)

#     department_id = db.Column(db.Integer, db.ForeignKey('departments.id'),
#                               nullable=False)

#     # ------------------------------------------------------------------ #
#     #  STUDENT IDENTITY
#     # ------------------------------------------------------------------ #
#     # Roll number — unique identifier within the college
#     roll_number = db.Column(db.String(20), unique=True, nullable=False)

#     # Academic year they were admitted e.g. "2022-23"
#     admission_year = db.Column(db.String(9), nullable=False)

#     # ------------------------------------------------------------------ #
#     #  PROGRAM TYPE
#     #  'UG' = Under Graduate (B.Tech, B.Sc, B.Com etc.) → max 8 semesters
#     #  'PG' = Post Graduate  (M.Tech, M.Sc, MBA etc.)   → max 4 semesters
#     #
#     #  This field controls:
#     #    - How many semesters exist before graduation
#     #    - Validation in promotion logic (can't promote past max semester)
#     # ------------------------------------------------------------------ #
#     program_type = db.Column(
#         db.String(5),
#         nullable=False,
#         default='UG'
#         # Allowed: 'UG' or 'PG'
#     )

#     # ------------------------------------------------------------------ #
#     #  CURRENT SEMESTER
#     #  Starts at 1 when the student joins.
#     #  HOD promotes this number (e.g. 1 → 2) at the end of each semester.
#     #  Range: 1-8 for UG, 1-4 for PG.
#     # ------------------------------------------------------------------ #
#     semester = db.Column(db.Integer, nullable=False, default=1)

#     # ------------------------------------------------------------------ #
#     #  GRADUATION FIELDS
#     #
#     #  is_graduated:
#     #    False → active student, can be promoted, can log in
#     #    True  → graduated, cannot be promoted, User.is_active = False
#     #
#     #  graduation_semester:
#     #    NULL while student is active.
#     #    Set to the semester number at the time of graduation.
#     #    For UG: will be 6 or 8.  For PG: will be 4.
#     #
#     #  graduation_year:
#     #    NULL while active. Set to the calendar year of graduation.
#     #    Stored separately from semester for easy filtering in reports.
#     #
#     #  graduation_reason:
#     #    NULL while active. HOD writes a note when graduating.
#     #    Examples: "Completed programme", "Lateral exit after 6th sem"
#     #
#     #  graduated_at:
#     #    NULL while active. Timestamp of when the HOD clicked "Graduate".
#     #    Used for audit trail.
#     #
#     #  graduated_by_id:
#     #    Which HOD (Teacher) performed the graduation action.
#     #    Important for accountability — you know who graduated whom.
#     # ------------------------------------------------------------------ #
#     is_graduated       = db.Column(db.Boolean, default=False, nullable=False)
#     graduation_semester= db.Column(db.Integer,  nullable=True)
#     graduation_year    = db.Column(db.String(9), nullable=True)
#     graduation_reason  = db.Column(db.Text,      nullable=True)
#     graduated_at       = db.Column(db.DateTime,  nullable=True)
#     graduated_by_id    = db.Column(db.Integer,
#                                    db.ForeignKey('teachers.id'), nullable=True)

#     # ------------------------------------------------------------------ #
#     #  TIMESTAMPS
#     # ------------------------------------------------------------------ #
#     created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
#     updated_at = db.Column(db.DateTime, default=datetime.utcnow,
#                            onupdate=datetime.utcnow, nullable=False)

#     # ------------------------------------------------------------------ #
#     #  RELATIONSHIPS
#     # ------------------------------------------------------------------ #
#     user            = db.relationship('User', back_populates='student_profile')
#     department      = db.relationship('Department', back_populates='students')
#     graduated_by    = db.relationship('Teacher', foreign_keys=[graduated_by_id])

#     # All attendance records FOR this student
#     attendance_records = db.relationship('Attendance', back_populates='student',
#                                          lazy='dynamic',
#                                          cascade='all, delete-orphan')

#     # ------------------------------------------------------------------ #
#     #  COMPUTED PROPERTIES
#     # ------------------------------------------------------------------ #
#     @property
#     def max_semester(self):
#         """
#         Returns the highest semester this student can reach.
#         UG → 8 semesters,  PG → 4 semesters.
#         Used in promotion validation.
#         """
#         return 8 if self.program_type == 'UG' else 4

#     @property
#     def valid_graduation_semesters(self):
#         """
#         Returns which semesters are valid for graduation.
#         UG → can graduate at 6th OR 8th semester
#         PG → can only graduate at 4th semester
#         """
#         if self.program_type == 'UG':
#             return [6, 8]
#         return [4]

#     @property
#     def can_be_promoted(self):
#         """
#         Returns True if the student is eligible for semester promotion.
#         Conditions to allow promotion:
#           1. Not already graduated
#           2. Not yet at the maximum semester
#         """
#         if self.is_graduated:
#             return False
#         return self.semester < self.max_semester

#     @property
#     def can_be_graduated(self):
#         """
#         Returns True if the student is at a valid graduation semester.
#         The HOD still has to manually trigger graduation — this just
#         tells us if it's ALLOWED at the current semester.
#         """
#         if self.is_graduated:
#             return False
#         return self.semester in self.valid_graduation_semesters

#     @property
#     def full_name(self):
#         return self.user.full_name if self.user else 'Unknown'

#     @property
#     def email(self):
#         return self.user.email if self.user else ''

#     @property
#     def attendance_percentage(self):
#         """
#         Attendance % for current semester using the correct formula:

#           attended  = classes where status = 'present'
#           conducted = classes where status NOT IN ('leave', 'event')
#                       (leave/event days excluded from both numerator & denominator)
#           percentage = attended / conducted × 100

#         Returns 0.0 if no classes have been conducted yet.
#         """
#         records = self.attendance_records.filter_by(
#             semester=self.semester
#         ).all()

#         # Only count classes that were actually conducted
#         conducted = [r for r in records if r.status not in ('leave', 'event')]
#         if not conducted:
#             return 0.0

#         attended = sum(1 for r in conducted if r.status == 'present')
#         return round((attended / len(conducted)) * 100, 2)

#     def attendance_percentage_for_subject(self, subject_id):
#         """
#         Attendance % for a specific subject.
#         Same leave/event exclusion logic as overall percentage.
#         """
#         from app.models.attendance import Attendance
#         records = self.attendance_records.filter_by(
#             subject_id=subject_id
#         ).all()
#         conducted = [r for r in records if r.status not in ('leave', 'event')]
#         if not conducted:
#             return 0.0
#         attended = sum(1 for r in conducted if r.status == 'present')
#         return round((attended / len(conducted)) * 100, 2)

#     def __repr__(self):
#         return f'<Student {self.roll_number} - Sem {self.semester} [{self.program_type}]>'


#######-----------updated---------------
from app import db
from datetime import datetime


class Student(db.Model):
    """
    Student profile — linked 1-to-1 with a User account.

    KEY DESIGN DECISIONS:
    ─────────────────────
    1. program_type (UG/PG) determines the graduation semester ceiling.
       UG can graduate at semester 6 OR 8 (honours/lateral entry).
       PG graduates at semester 4.

    2. semester is the CURRENT semester the student is in.
       It is manually promoted by the HOD — the system never auto-promotes.

    3. is_graduated=True makes the student inactive. They can no longer
       be promoted, and their User.is_active is set to False so they
       cannot log in. BUT their data is permanently preserved.

    4. graduation_semester records WHICH semester they graduated from.
       This is important for transcripts and historical records.

    5. graduation_reason is a free-text note the HOD writes when
       graduating a student (e.g. "Completed 8 semesters with honours").
    """
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)

    # ------------------------------------------------------------------ #
    #  FOREIGN KEYS
    # ------------------------------------------------------------------ #
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        unique=True, nullable=False)

    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'),
                              nullable=False)

    # ------------------------------------------------------------------ #
    #  STUDENT IDENTITY
    # ------------------------------------------------------------------ #
    # Roll number — unique identifier within the college
    roll_number = db.Column(db.String(20), unique=True, nullable=False)

    # Academic year they were admitted e.g. "2022-23"
    admission_year = db.Column(db.String(9), nullable=False)

    # ------------------------------------------------------------------ #
    #  PROGRAM TYPE
    #  'UG' = Under Graduate (B.Tech, B.Sc, B.Com etc.) → max 8 semesters
    #  'PG' = Post Graduate  (M.Tech, M.Sc, MBA etc.)   → max 4 semesters
    #
    #  This field controls:
    #    - How many semesters exist before graduation
    #    - Validation in promotion logic (can't promote past max semester)
    # ------------------------------------------------------------------ #
    program_type = db.Column(
        db.String(5),
        nullable=False,
        default='UG'
        # Allowed: 'UG' or 'PG'
    )

    # ------------------------------------------------------------------ #
    #  CURRENT SEMESTER
    #  Starts at 1 when the student joins.
    #  HOD promotes this number (e.g. 1 → 2) at the end of each semester.
    #  Range: 1-8 for UG, 1-4 for PG.
    # ------------------------------------------------------------------ #
    semester = db.Column(db.Integer, nullable=False, default=1)

    # ------------------------------------------------------------------ #
    #  GRADUATION FIELDS
    #
    #  is_graduated:
    #    False → active student, can be promoted, can log in
    #    True  → graduated, cannot be promoted, User.is_active = False
    #
    #  graduation_semester:
    #    NULL while student is active.
    #    Set to the semester number at the time of graduation.
    #    For UG: will be 6 or 8.  For PG: will be 4.
    #
    #  graduation_year:
    #    NULL while active. Set to the calendar year of graduation.
    #    Stored separately from semester for easy filtering in reports.
    #
    #  graduation_reason:
    #    NULL while active. HOD writes a note when graduating.
    #    Examples: "Completed programme", "Lateral exit after 6th sem"
    #
    #  graduated_at:
    #    NULL while active. Timestamp of when the HOD clicked "Graduate".
    #    Used for audit trail.
    #
    #  graduated_by_id:
    #    Which HOD (Teacher) performed the graduation action.
    #    Important for accountability — you know who graduated whom.
    # ------------------------------------------------------------------ #
    is_graduated       = db.Column(db.Boolean, default=False, nullable=False)
    graduation_semester= db.Column(db.Integer,  nullable=True)
    graduation_year    = db.Column(db.String(9), nullable=True)
    graduation_reason  = db.Column(db.Text,      nullable=True)
    graduated_at       = db.Column(db.DateTime,  nullable=True)
    graduated_by_id    = db.Column(db.Integer,
                                   db.ForeignKey('teachers.id'), nullable=True)

    # ------------------------------------------------------------------ #
    #  TIMESTAMPS
    # ------------------------------------------------------------------ #
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # ------------------------------------------------------------------ #
    #  RELATIONSHIPS
    # ------------------------------------------------------------------ #
    user            = db.relationship('User', back_populates='student_profile')
    department      = db.relationship('Department', back_populates='students')
    graduated_by    = db.relationship('Teacher', foreign_keys=[graduated_by_id])

    # All attendance records FOR this student
    attendance_records = db.relationship('Attendance', back_populates='student',
                                         lazy='dynamic',
                                         cascade='all, delete-orphan')

    # ------------------------------------------------------------------ #
    #  COMPUTED PROPERTIES
    # ------------------------------------------------------------------ #
    @property
    def max_semester(self):
        """
        Returns the highest semester this student can reach.
        UG → 8 semesters,  PG → 4 semesters.
        Used in promotion validation.
        """
        return 8 if self.program_type == 'UG' else 4

    @property
    def valid_graduation_semesters(self):
        """
        Returns which semesters are valid for graduation.
        UG → can graduate at 6th OR 8th semester
        PG → can only graduate at 4th semester
        """
        if self.program_type == 'UG':
            return [6, 8]
        return [4]

    @property
    def can_be_promoted(self):
        """
        Returns True if the student is eligible for semester promotion.
        Conditions to allow promotion:
          1. Not already graduated
          2. Not yet at the maximum semester
        """
        if self.is_graduated:
            return False
        return self.semester < self.max_semester

    @property
    def can_be_graduated(self):
        """
        Returns True if the student is at a valid graduation semester.
        The HOD still has to manually trigger graduation — this just
        tells us if it's ALLOWED at the current semester.
        """
        if self.is_graduated:
            return False
        return self.semester in self.valid_graduation_semesters

    @property
    def full_name(self):
        return self.user.full_name if self.user else 'Unknown'

    @property
    def email(self):
        return self.user.email if self.user else ''

    @property
    def attendance_percentage(self):
        """
        Attendance % for current semester using the correct formula:

          attended  = classes where status = 'present'
          conducted = classes where status NOT IN ('leave', 'event')
                      (leave/event days excluded from both numerator & denominator)
          percentage = attended / conducted × 100

        Returns 0.0 if no classes have been conducted yet.
        """
        records = self.attendance_records.filter_by(
            semester=self.semester
        ).all()

        # Only count classes that were actually conducted
        conducted = [r for r in records if r.status not in ('leave', 'event')]
        if not conducted:
            return 0.0

        attended = sum(1 for r in conducted if r.status == 'present')
        return round((attended / len(conducted)) * 100, 2)

    def attendance_percentage_for_subject(self, subject_id):
        """
        Attendance % for a specific subject.
        Same leave/event exclusion logic as overall percentage.
        """
        from app.models.attendance import Attendance
        records = self.attendance_records.filter_by(
            subject_id=subject_id
        ).all()
        conducted = [r for r in records if r.status not in ('leave', 'event')]
        if not conducted:
            return 0.0
        attended = sum(1 for r in conducted if r.status == 'present')
        return round((attended / len(conducted)) * 100, 2)

    def __repr__(self):
        return f'<Student {self.roll_number} - Sem {self.semester} [{self.program_type}]>'
