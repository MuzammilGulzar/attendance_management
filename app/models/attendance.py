# from app import db
# from datetime import datetime


# class Attendance(db.Model):
#     """
#     ONE row = ONE student's attendance for ONE class on ONE date.

#     EDIT POLICY:
#       - Teacher can INSERT new records (mark attendance)
#       - Teacher CANNOT edit existing records
#       - Only HOD can UPDATE existing records (with mandatory reason)
#       - All HOD edits are tracked: who, when, original value

#     UNIQUE CONSTRAINT:
#       student + subject + date must be unique.
#       A student cannot have two records for the same subject on the same day.

#     STATUS VALUES (6 total):
#     ─────────────────────────────────────────────────────────────────────
#     'present'  → student attended                      (counts both sides)
#     'absent'   → student did not attend                (counts conducted only)
#     'leave'    → authorised leave — medical/personal   (excluded from both)
#     'event'    → official college duty                 (excluded from both)
#     'no_class' → class cancelled / holiday / Sunday    (excluded from both)
#     'pending'  → QR scanned, awaiting teacher review   (excluded from both)

#     PERCENTAGE FORMULA:
#       conducted = rows where status IN ('present', 'absent')
#       present   = rows where status == 'present'
#       pct       = present / conducted × 100

#       'leave', 'event', 'no_class', 'pending' are excluded from BOTH
#       sides — they are neutral and do not affect the percentage at all.

#     'pending' is a TEMPORARY state:
#       Created when a student submits via QR scan.
#       Must be resolved by the teacher (→ present / leave / event / no_class).
#       While pending, the record does not affect the student's %.

#     'no_class' is set by the TEACHER ONLY:
#       Used during QR review when the teacher decides the session
#       is cancelled (holiday, Sunday, power cut, etc.).
#       Can also be set retroactively for a batch.
#     """
#     __tablename__ = 'attendance'

#     __table_args__ = (
#         db.UniqueConstraint(
#             'student_id', 'subject_id', 'date',
#             name='uq_student_subject_date'
#         ),
#     )

#     id = db.Column(db.Integer, primary_key=True)

#     # ── Foreign keys ─────────────────────────────────────────────────
#     student_id   = db.Column(db.Integer, db.ForeignKey('students.id'),
#                              nullable=False, index=True)
#     subject_id   = db.Column(db.Integer, db.ForeignKey('subjects.id'),
#                              nullable=False, index=True)
#     marked_by_id = db.Column(db.Integer, db.ForeignKey('teachers.id'),
#                              nullable=False)
#     date         = db.Column(db.Date,    nullable=False, index=True)

#     # ── Status ───────────────────────────────────────────────────────
#     # String(10) fits all six values: longest is 'no_class' (8 chars)
#     status = db.Column(
#         db.String(10),
#         nullable=False,
#         default='absent'
#         # Allowed: 'present', 'absent', 'leave', 'event', 'no_class', 'pending'
#     )

#     semester = db.Column(db.Integer, nullable=False)

#     # ── HOD edit tracking ────────────────────────────────────────────
#     is_edited       = db.Column(db.Boolean,  default=False, nullable=False)
#     edit_reason     = db.Column(db.Text,     nullable=True)
#     edited_by_id    = db.Column(db.Integer,
#                                 db.ForeignKey('teachers.id'), nullable=True)
#     edited_at       = db.Column(db.DateTime, nullable=True)
#     original_status = db.Column(db.String(10), nullable=True)

#     # ── Teacher QR review tracking ───────────────────────────────────
#     # When a pending record is reviewed, we record who reviewed it and when.
#     # This is separate from HOD edits — it's the teacher confirming a QR scan.
#     is_qr_scan       = db.Column(db.Boolean,  default=False, nullable=False)
#     # True  → this record was created by a student QR scan
#     # False → this record was created by the teacher manually
#     # Needed so the review page can filter to QR submissions only.

#     reviewed_by_id   = db.Column(db.Integer,
#                                  db.ForeignKey('teachers.id'), nullable=True)
#     reviewed_at      = db.Column(db.DateTime, nullable=True)
#     # Stores who finalised the pending record and when.

#     created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

#     # ── Relationships ────────────────────────────────────────────────
#     student    = db.relationship('Student',  back_populates='attendance_records')
#     subject    = db.relationship('Subject',  back_populates='attendance_records')
#     marked_by  = db.relationship('Teacher',  foreign_keys=[marked_by_id],
#                                  back_populates='attendance_records')
#     edited_by  = db.relationship('Teacher',  foreign_keys=[edited_by_id])
#     reviewed_by = db.relationship('Teacher', foreign_keys=[reviewed_by_id])

#     # ── Class-level constants ────────────────────────────────────────
#     # All statuses the DB will ever store.
#     VALID_STATUSES = ('present', 'absent', 'leave', 'event', 'no_class', 'pending')

#     # Statuses a teacher can set during QR review (excludes 'absent' and 'pending').
#     # During review, unscanned students are simply absent — teacher doesn't
#     # need to explicitly mark them. 'absent' is handled by the review service.
#     REVIEW_STATUSES = ('present', 'absent', 'leave', 'event', 'no_class')

#     # Statuses a teacher can set during manual marking.
#     # Excludes 'pending' (that's QR-only) and 'no_class' is allowed
#     # so teacher can mark a holiday retroactively.
#     MANUAL_STATUSES = ('present', 'absent', 'leave', 'event', 'no_class')

#     # ── Helper methods ───────────────────────────────────────────────

#     def apply_hod_edit(self, new_status, reason, hod_teacher):
#         """
#         HOD edits a finalised attendance record.
#         Saves original value, records who/when.
#         Only call this for HOD edits — not for teacher QR review.
#         """
#         self.original_status = self.status
#         self.status          = new_status
#         self.edit_reason     = reason
#         self.edited_by_id    = hod_teacher.id
#         self.edited_at       = datetime.utcnow()
#         self.is_edited       = True

#     def apply_teacher_review(self, new_status, teacher):
#         """
#         Teacher finalises a pending QR scan record.
#         Changes status from 'pending' to the confirmed status.
#         Records who reviewed and when.

#         Called by: review_qr_submissions() in teacher_service.py

#         Parameters:
#           new_status — one of REVIEW_STATUSES
#           teacher    — Teacher object (not User) of the reviewing teacher
#         """
#         self.status         = new_status
#         self.reviewed_by_id = teacher.id
#         self.reviewed_at    = datetime.utcnow()

#     @property
#     def is_present(self):
#         return self.status == 'present'

#     @property
#     def is_pending(self):
#         """True while the QR scan hasn't been reviewed by the teacher yet."""
#         return self.status == 'pending'

#     @property
#     def is_neutral(self):
#         """
#         Neutral statuses are excluded from the attendance percentage entirely.
#         'leave', 'event', 'no_class', 'pending' all fall here.

#         'pending' is neutral because the final outcome is not yet decided.
#         Including it as absent before review would unfairly hurt the student.
#         Including it as present before review would let unreviewed QRs inflate %.
#         Neutral is the only safe choice until the teacher confirms.
#         """
#         return self.status in ('leave', 'event', 'no_class', 'pending')

#     @property
#     def counts_as_conducted(self):
#         """
#         True if this record counts towards the 'classes conducted' denominator.
#         Only 'present' and 'absent' count as conducted.
#         Everything else is excluded from both sides of the formula.
#         """
#         return self.status in ('present', 'absent')

#     def __repr__(self):
#         return (f'<Attendance student={self.student_id} '
#                 f'subject={self.subject_id} '
#                 f'date={self.date} status={self.status}>')
    


###########-----------fix minor bugs----------
from app import db
from datetime import datetime


class Attendance(db.Model):
    """
    ONE row = ONE student's attendance for ONE class on ONE date.

    EDIT POLICY:
      - Teacher can INSERT new records (mark attendance)
      - Teacher CANNOT edit existing records
      - Only HOD can UPDATE existing records (with mandatory reason)
      - All HOD edits are tracked: who, when, original value

    UNIQUE CONSTRAINT:
      student + subject + date must be unique.
      A student cannot have two records for the same subject on the same day.

    STATUS VALUES (6 total):
    ─────────────────────────────────────────────────────────────────────
    'present'  → student attended                      (counts both sides)
    'absent'   → student did not attend                (counts conducted only)
    'leave'    → authorised leave — medical/personal   (excluded from both)
    'event'    → official college duty                 (excluded from both)
    'no_class' → class cancelled / holiday / Sunday    (excluded from both)
    'pending'  → QR scanned, awaiting teacher review   (excluded from both)

    PERCENTAGE FORMULA:
      conducted = rows where status IN ('present', 'absent')
      present   = rows where status == 'present'
      pct       = present / conducted × 100

      'leave', 'event', 'no_class', 'pending' are excluded from BOTH
      sides — they are neutral and do not affect the percentage at all.

    'pending' is a TEMPORARY state:
      Created when a student submits via QR scan.
      Must be resolved by the teacher (→ present / leave / event / no_class).
      While pending, the record does not affect the student's %.

    'no_class' is set by the TEACHER ONLY:
      Used during QR review when the teacher decides the session
      is cancelled (holiday, Sunday, power cut, etc.).
      Can also be set retroactively for a batch.
    """
    __tablename__ = 'attendance'

    __table_args__ = (
        db.UniqueConstraint(
            'student_id', 'subject_id', 'date',
            name='uq_student_subject_date'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)

    # ── Foreign keys ─────────────────────────────────────────────────
    student_id   = db.Column(db.Integer, db.ForeignKey('students.id'),
                             nullable=False, index=True)
    subject_id   = db.Column(db.Integer, db.ForeignKey('subjects.id'),
                             nullable=False, index=True)
    marked_by_id = db.Column(db.Integer, db.ForeignKey('teachers.id'),
                             nullable=False)
    date         = db.Column(db.Date,    nullable=False, index=True)

    # ── Status ───────────────────────────────────────────────────────
    # String(10) fits all six values: longest is 'no_class' (8 chars)
    status = db.Column(
        db.String(10),
        nullable=False,
        default='absent'
        # Allowed: 'present', 'absent', 'leave', 'event', 'no_class', 'pending'
    )

    semester = db.Column(db.Integer, nullable=False)

    # ── HOD edit tracking ────────────────────────────────────────────
    is_edited       = db.Column(db.Boolean,  default=False, nullable=False)
    edit_reason     = db.Column(db.Text,     nullable=True)
    edited_by_id    = db.Column(db.Integer,
                                db.ForeignKey('teachers.id'), nullable=True)
    edited_at       = db.Column(db.DateTime, nullable=True)
    original_status = db.Column(db.String(10), nullable=True)

    # ── Teacher QR review tracking ───────────────────────────────────
    # When a pending record is reviewed, we record who reviewed it and when.
    # This is separate from HOD edits — it's the teacher confirming a QR scan.
    is_qr_scan       = db.Column(db.Boolean,  default=False, nullable=False)
    # True  → this record was created by a student QR scan
    # False → this record was created by the teacher manually
    # Needed so the review page can filter to QR submissions only.

    reviewed_by_id   = db.Column(db.Integer,
                                 db.ForeignKey('teachers.id'), nullable=True)
    reviewed_at      = db.Column(db.DateTime, nullable=True)
    # Stores who finalised the pending record and when.

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ────────────────────────────────────────────────
    student    = db.relationship('Student',  back_populates='attendance_records')
    subject    = db.relationship('Subject',  back_populates='attendance_records')
    marked_by  = db.relationship('Teacher',  foreign_keys=[marked_by_id],
                                 back_populates='attendance_records')
    edited_by  = db.relationship('Teacher',  foreign_keys=[edited_by_id])
    reviewed_by = db.relationship('Teacher', foreign_keys=[reviewed_by_id])

    # ── Class-level constants ────────────────────────────────────────
    # All statuses the DB will ever store.
    VALID_STATUSES = ('present', 'absent', 'leave', 'event', 'no_class', 'pending')

    # Statuses a teacher can set during QR review (excludes 'absent' and 'pending').
    # During review, unscanned students are simply absent — teacher doesn't
    # need to explicitly mark them. 'absent' is handled by the review service.
    REVIEW_STATUSES = ('present', 'leave', 'event', 'no_class')

    # Statuses a teacher can set during manual marking.
    # Excludes 'pending' (that's QR-only) and 'no_class' is allowed
    # so teacher can mark a holiday retroactively.
    MANUAL_STATUSES = ('present', 'absent', 'leave', 'event', 'no_class')

    # ── Helper methods ───────────────────────────────────────────────

    def apply_hod_edit(self, new_status, reason, hod_teacher):
        """
        HOD edits a finalised attendance record.
        Saves original value, records who/when.
        Only call this for HOD edits — not for teacher QR review.
        """
        self.original_status = self.status
        self.status          = new_status
        self.edit_reason     = reason
        self.edited_by_id    = hod_teacher.id
        self.edited_at       = datetime.utcnow()
        self.is_edited       = True

    def apply_teacher_review(self, new_status, teacher):
        """
        Teacher finalises a pending QR scan record.
        Changes status from 'pending' to the confirmed status.
        Records who reviewed and when.

        Called by: review_qr_submissions() in teacher_service.py

        Parameters:
          new_status — one of REVIEW_STATUSES
          teacher    — Teacher object (not User) of the reviewing teacher
        """
        self.status         = new_status
        self.reviewed_by_id = teacher.id
        self.reviewed_at    = datetime.utcnow()

    @property
    def is_present(self):
        return self.status == 'present'

    @property
    def is_pending(self):
        """True while the QR scan hasn't been reviewed by the teacher yet."""
        return self.status == 'pending'

    @property
    def is_neutral(self):
        """
        Neutral statuses are excluded from the attendance percentage entirely.
        'leave', 'event', 'no_class', 'pending' all fall here.

        'pending' is neutral because the final outcome is not yet decided.
        Including it as absent before review would unfairly hurt the student.
        Including it as present before review would let unreviewed QRs inflate %.
        Neutral is the only safe choice until the teacher confirms.
        """
        return self.status in ('leave', 'event', 'no_class', 'pending')

    @property
    def counts_as_conducted(self):
        """
        True if this record counts towards the 'classes conducted' denominator.
        Only 'present' and 'absent' count as conducted.
        Everything else is excluded from both sides of the formula.
        """
        return self.status in ('present', 'absent')

    def __repr__(self):
        return (f'<Attendance student={self.student_id} '
                f'subject={self.subject_id} '
                f'date={self.date} status={self.status}>')