# from app import db
# from datetime import datetime


# class Attendance(db.Model):
#     """
#     ONE row = ONE student's attendance for ONE class on ONE date.

#     This is the core transactional table of the entire system.
#     Every time a teacher marks attendance, rows are inserted here.

#     EDIT POLICY (enforced in service layer):
#       - Teacher can INSERT new records (mark attendance)
#       - Teacher CANNOT edit existing records
#       - Only HOD can UPDATE (edit) existing records
#       - Every HOD edit MUST include a reason (stored in edit_reason)
#       - All edits are tracked with who edited and when

#     UNIQUE CONSTRAINT:
#       student + subject + date must be unique.
#       A student cannot have two attendance records for the same
#       subject on the same day — the DB enforces this automatically.
#     """
#     __tablename__ = 'attendance'

#     # Composite unique constraint — prevents duplicate entries
#     __table_args__ = (
#         db.UniqueConstraint(
#             'student_id', 'subject_id', 'date',
#             name='uq_student_subject_date'
#         ),
#     )

#     id = db.Column(db.Integer, primary_key=True)

#     # ------------------------------------------------------------------ #
#     #  FOREIGN KEYS — who, what, when
#     # ------------------------------------------------------------------ #
#     student_id = db.Column(db.Integer, db.ForeignKey('students.id'),
#                            nullable=False, index=True)

#     subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'),
#                            nullable=False, index=True)

#     # Which teacher marked this attendance entry
#     marked_by_id = db.Column(db.Integer, db.ForeignKey('teachers.id'),
#                              nullable=False)

#     # ------------------------------------------------------------------ #
#     #  CLASS DATE
#     #  Stored as a Python date (not datetime) because we only care about
#     #  the day, not the exact time of the class.
#     #  index=True because we query by date very frequently.
#     # ------------------------------------------------------------------ #
#     date = db.Column(db.Date, nullable=False, index=True)

#     # ------------------------------------------------------------------ #
#     #  ATTENDANCE STATUS — four official values:
#     #  'present' → student attended the class
#     #  'absent'  → student did not attend (counted against percentage)
#     #  'leave'   → authorised leave (medical, personal) — does NOT count
#     #              against percentage but is tracked separately
#     #  'event'   → student was on official college duty (sports, seminar,
#     #              fest etc.) — does NOT count against percentage
#     #
#     #  Percentage formula:
#     #    attended_classes  = rows where status IN ('present')
#     #    conducted_classes = rows where status NOT IN ('leave', 'event')
#     #    percentage        = attended / conducted × 100
#     #
#     #    leave and event days are excluded from BOTH numerator AND
#     #    denominator — they are neutral and do not help or hurt %.
#     # ------------------------------------------------------------------ #
#     status = db.Column(
#         db.String(10),
#         nullable=False,
#         default='absent'
#         # Allowed: 'present', 'absent', 'leave', 'event'
#     )

#     # ------------------------------------------------------------------ #
#     #  SEMESTER  — snapshot of which semester the student was in
#     #  when this record was created. Important because if a student is
#     #  promoted, we still need to know which semester this class was for.
#     # ------------------------------------------------------------------ #
#     semester = db.Column(db.Integer, nullable=False)

#     # ------------------------------------------------------------------ #
#     #  EDIT TRACKING (HOD edits only)
#     #
#     #  is_edited:
#     #    False → original entry, never changed
#     #    True  → HOD has modified this record at least once
#     #
#     #  edit_reason:
#     #    REQUIRED when is_edited=True. HOD must explain why they changed
#     #    the record. e.g. "Student submitted medical certificate"
#     #
#     #  edited_by_id:
#     #    Which HOD (Teacher) made the edit.
#     #
#     #  edited_at:
#     #    When was the edit made? Full datetime for precise audit trail.
#     #
#     #  original_status:
#     #    What was the status BEFORE the HOD changed it?
#     #    Stored for complete audit trail — you can see before & after.
#     # ------------------------------------------------------------------ #
#     is_edited       = db.Column(db.Boolean,  default=False, nullable=False)
#     edit_reason     = db.Column(db.Text,     nullable=True)
#     edited_by_id    = db.Column(db.Integer,
#                                 db.ForeignKey('teachers.id'), nullable=True)
#     edited_at       = db.Column(db.DateTime, nullable=True)
#     original_status = db.Column(db.String(10), nullable=True)

#     # When was this row first created (i.e. when teacher marked it)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

#     # ------------------------------------------------------------------ #
#     #  RELATIONSHIPS
#     # ------------------------------------------------------------------ #
#     student    = db.relationship('Student', back_populates='attendance_records')
#     subject    = db.relationship('Subject', back_populates='attendance_records')
#     marked_by  = db.relationship('Teacher', foreign_keys=[marked_by_id],
#                                  back_populates='attendance_records')
#     edited_by  = db.relationship('Teacher', foreign_keys=[edited_by_id])

#     # ------------------------------------------------------------------ #
#     #  HELPER METHODS
#     # ------------------------------------------------------------------ #
#     def apply_hod_edit(self, new_status, reason, hod_teacher):
#         """
#         HOD calls this to edit an attendance record.
#         Automatically saves the original value and records who/when.

#         Usage:
#           record.apply_hod_edit('present', 'Medical cert submitted', hod)
#         """
#         self.original_status = self.status   # save what it was before
#         self.status          = new_status
#         self.edit_reason     = reason
#         self.edited_by_id    = hod_teacher.id
#         self.edited_at       = datetime.utcnow()
#         self.is_edited       = True

#     # All four valid status values as a class-level constant
#     VALID_STATUSES = ('present', 'absent', 'leave', 'event')

#     @property
#     def is_present(self):
#         return self.status == 'present'

#     @property
#     def is_neutral(self):
#         """
#         Leave and Event are 'neutral' — they are excluded from
#         the attendance percentage calculation entirely.
#         Neither helps the student (like present) nor hurts them (like absent).
#         """
#         return self.status in ('leave', 'event')

#     @property
#     def counts_as_conducted(self):
#         """
#         Returns True if this class counts towards 'total classes conducted'.
#         Leave and Event days do NOT count — percentage denominator excludes them.
#         """
#         return self.status not in ('leave', 'event')

#     def __repr__(self):
#         return (f'<Attendance student={self.student_id} '
#                 f'subject={self.subject_id} '
#                 f'date={self.date} status={self.status}>')


#############--------------updated-------------------
from app import db
from datetime import datetime


class Attendance(db.Model):
    """
    ONE row = ONE student's attendance for ONE class on ONE date.

    This is the core transactional table of the entire system.
    Every time a teacher marks attendance, rows are inserted here.

    EDIT POLICY (enforced in service layer):
      - Teacher can INSERT new records (mark attendance)
      - Teacher CANNOT edit existing records
      - Only HOD can UPDATE (edit) existing records
      - Every HOD edit MUST include a reason (stored in edit_reason)
      - All edits are tracked with who edited and when

    UNIQUE CONSTRAINT:
      student + subject + date must be unique.
      A student cannot have two attendance records for the same
      subject on the same day — the DB enforces this automatically.
    """
    __tablename__ = 'attendance'

    # Composite unique constraint — prevents duplicate entries
    __table_args__ = (
        db.UniqueConstraint(
            'student_id', 'subject_id', 'date',
            name='uq_student_subject_date'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    # ------------------------------------------------------------------ #
    #  FOREIGN KEYS — who, what, when
    # ------------------------------------------------------------------ #
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'),
                           nullable=False, index=True)

    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'),
                           nullable=False, index=True)

    # Which teacher marked this attendance entry
    marked_by_id = db.Column(db.Integer, db.ForeignKey('teachers.id'),
                             nullable=False)

    # ------------------------------------------------------------------ #
    #  CLASS DATE
    #  Stored as a Python date (not datetime) because we only care about
    #  the day, not the exact time of the class.
    #  index=True because we query by date very frequently.
    # ------------------------------------------------------------------ #
    date = db.Column(db.Date, nullable=False, index=True)

    # ------------------------------------------------------------------ #
    #  ATTENDANCE STATUS — four official values:
    #  'present' → student attended the class
    #  'absent'  → student did not attend (counted against percentage)
    #  'leave'   → authorised leave (medical, personal) — does NOT count
    #              against percentage but is tracked separately
    #  'event'   → student was on official college duty (sports, seminar,
    #              fest etc.) — does NOT count against percentage
    #
    #  Percentage formula:
    #    attended_classes  = rows where status IN ('present')
    #    conducted_classes = rows where status NOT IN ('leave', 'event')
    #    percentage        = attended / conducted × 100
    #
    #    leave and event days are excluded from BOTH numerator AND
    #    denominator — they are neutral and do not help or hurt %.
    # ------------------------------------------------------------------ #
    status = db.Column(
        db.String(10),
        nullable=False,
        default='absent'
        # Allowed: 'present', 'absent', 'leave', 'event'
    )

    # ------------------------------------------------------------------ #
    #  SEMESTER  — snapshot of which semester the student was in
    #  when this record was created. Important because if a student is
    #  promoted, we still need to know which semester this class was for.
    # ------------------------------------------------------------------ #
    semester = db.Column(db.Integer, nullable=False)

    # ------------------------------------------------------------------ #
    #  EDIT TRACKING (HOD edits only)
    #
    #  is_edited:
    #    False → original entry, never changed
    #    True  → HOD has modified this record at least once
    #
    #  edit_reason:
    #    REQUIRED when is_edited=True. HOD must explain why they changed
    #    the record. e.g. "Student submitted medical certificate"
    #
    #  edited_by_id:
    #    Which HOD (Teacher) made the edit.
    #
    #  edited_at:
    #    When was the edit made? Full datetime for precise audit trail.
    #
    #  original_status:
    #    What was the status BEFORE the HOD changed it?
    #    Stored for complete audit trail — you can see before & after.
    # ------------------------------------------------------------------ #
    is_edited       = db.Column(db.Boolean,  default=False, nullable=False)
    edit_reason     = db.Column(db.Text,     nullable=True)
    edited_by_id    = db.Column(db.Integer,
                                db.ForeignKey('teachers.id'), nullable=True)
    edited_at       = db.Column(db.DateTime, nullable=True)
    original_status = db.Column(db.String(10), nullable=True)

    # When was this row first created (i.e. when teacher marked it)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ------------------------------------------------------------------ #
    #  RELATIONSHIPS
    # ------------------------------------------------------------------ #
    student    = db.relationship('Student', back_populates='attendance_records')
    subject    = db.relationship('Subject', back_populates='attendance_records')
    marked_by  = db.relationship('Teacher', foreign_keys=[marked_by_id],
                                 back_populates='attendance_records')
    edited_by  = db.relationship('Teacher', foreign_keys=[edited_by_id])

    # ------------------------------------------------------------------ #
    #  HELPER METHODS
    # ------------------------------------------------------------------ #
    def apply_hod_edit(self, new_status, reason, hod_teacher):
        """
        HOD calls this to edit an attendance record.
        Automatically saves the original value and records who/when.

        Usage:
          record.apply_hod_edit('present', 'Medical cert submitted', hod)
        """
        self.original_status = self.status   # save what it was before
        self.status          = new_status
        self.edit_reason     = reason
        self.edited_by_id    = hod_teacher.id
        self.edited_at       = datetime.utcnow()
        self.is_edited       = True

    # All four valid status values as a class-level constant
    VALID_STATUSES = ('present', 'absent', 'leave', 'event')

    @property
    def is_present(self):
        return self.status == 'present'

    @property
    def is_neutral(self):
        """
        Leave and Event are 'neutral' — they are excluded from
        the attendance percentage calculation entirely.
        Neither helps the student (like present) nor hurts them (like absent).
        """
        return self.status in ('leave', 'event')

    @property
    def counts_as_conducted(self):
        """
        Returns True if this class counts towards 'total classes conducted'.
        Leave and Event days do NOT count — percentage denominator excludes them.
        """
        return self.status not in ('leave', 'event')

    def __repr__(self):
        return (f'<Attendance student={self.student_id} '
                f'subject={self.subject_id} '
                f'date={self.date} status={self.status}>')
