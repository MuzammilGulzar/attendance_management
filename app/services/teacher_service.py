# """
# TEACHER SERVICE
# ===============
# Business logic for the teacher dashboard.

# Covers:
#   1. Dashboard data — subjects, today's status, stats
#   2. Attendance marking — insert-only, no edits, duplicate prevention
#   3. Attendance history — what was marked on each date
#   4. Student roster — who is enrolled in a subject's semester

# CORE RULES enforced here:
#   R1. ONE record per student per subject per day (DB unique constraint +
#       service-level check)
#   R2. Teacher can only mark attendance for subjects ASSIGNED to them
#       (enforced by @teacher_owns_subject decorator + service ownership check)
#   R3. Teacher CANNOT edit any existing attendance record — attempt returns error
#   R4. 'leave' and 'event' statuses do NOT affect attendance percentage
#   R5. A teacher can mark attendance for a past date (if they forgot)
#       but not for a future date
# """

# from datetime import date, datetime, timedelta
# from app import db
# from app.models.attendance import Attendance
# from app.models.student    import Student
# from app.models.subject    import Subject
# from app.models.teacher    import Teacher
# from app.models.user       import User


# # ══════════════════════════════════════════════════════════════════════
# #  CONSTANTS
# # ══════════════════════════════════════════════════════════════════════

# VALID_STATUSES = ('present', 'absent', 'leave', 'event')

# STATUS_LABELS = {
#     'present': 'Present',
#     'absent' : 'Absent',
#     'leave'  : 'Leave',
#     'event'  : 'Event / Duty',
# }

# STATUS_COLORS = {
#     'present': 'success',
#     'absent' : 'danger',
#     'leave'  : 'warning',
#     'event'  : 'info',
# }

# # How many past days a teacher can backfill attendance for
# MAX_BACKFILL_DAYS = 7


# # ══════════════════════════════════════════════════════════════════════
# #  HELPER
# # ══════════════════════════════════════════════════════════════════════

# def _get_teacher(teacher_user):
#     """Get the Teacher profile for the logged-in user."""
#     return Teacher.query.filter_by(user_id=teacher_user.id).first()


# def _get_enrolled_students(subject):
#     """
#     Return all active non-graduated students who are enrolled in
#     the semester/program/department that this subject belongs to.
#     """
#     return (
#         Student.query
#         .filter_by(
#             department_id = subject.department_id,
#             semester      = subject.semester,
#             program_type  = subject.program_type,
#             is_graduated  = False,
#         )
#         .join(Student.user)
#         .filter(User.is_active == True)
#         .order_by(Student.roll_number)
#         .all()
#     )


# # ══════════════════════════════════════════════════════════════════════
# #  DASHBOARD DATA
# # ══════════════════════════════════════════════════════════════════════

# def get_teacher_dashboard_data(teacher_user):
#     """
#     Aggregates everything the teacher dashboard needs in one call.

#     Returns a dict with:
#       - teacher profile
#       - their subjects with today's marking status
#       - recent attendance activity
#       - subject-level stats
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return {'error': 'Teacher profile not found.'}

#     today = date.today()
#     subjects_data = []

#     for subject in teacher.subjects.order_by(Subject.semester, Subject.name).all():
#         students      = _get_enrolled_students(subject)
#         total_students = len(students)

#         # Check if attendance was already marked today for this subject
#         today_records = Attendance.query.filter_by(
#             subject_id=subject.id,
#             date=today
#         ).count()

#         already_marked_today = today_records > 0

#         # Overall subject attendance stats
#         all_records = subject.attendance_records.all()
#         conducted   = [r for r in all_records if r.status not in ('leave', 'event')]
#         present     = [r for r in conducted    if r.status == 'present']

#         subjects_data.append({
#             'subject'             : subject,
#             'total_students'      : total_students,
#             'already_marked_today': already_marked_today,
#             'today_marked_count'  : today_records,
#             'total_conducted'     : len(conducted),
#             'avg_attendance_pct'  : (
#                 round(len(present) / len(conducted) * 100, 1)
#                 if conducted else 0.0
#             ),
#         })

#     return {
#         'teacher'      : teacher,
#         'subjects_data': subjects_data,
#         'today'        : today,
#         'dept_name'    : teacher.department.name,
#         'dept_code'    : teacher.department.code,
#     }


# # ══════════════════════════════════════════════════════════════════════
# #  ATTENDANCE SESSION SETUP
# #  Prepares everything the mark-attendance form needs.
# # ══════════════════════════════════════════════════════════════════════

# def get_attendance_session(teacher_user, subject_id, for_date=None):
#     """
#     Prepare the data needed to show the mark-attendance form.

#     for_date: date object (defaults to today).
#               Teachers can submit for a past date (backfill window).

#     Returns a dict containing:
#       - subject
#       - students list with their current attendance status for this date
#       - whether this session already has records (already_marked)
#       - the date we're marking for
#       - valid statuses for the dropdown
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return None, 'Teacher profile not found.'

#     subject = Subject.query.get(subject_id)
#     if not subject:
#         return None, 'Subject not found.'

#     # Validate teacher owns this subject (HODs bypass this check)
#     if not teacher_user.is_hod:
#         assigned_ids = [s.id for s in teacher.subjects.all()]
#         if subject.id not in assigned_ids:
#             return None, 'You are not assigned to teach this subject.'

#     mark_date = for_date or date.today()

#     # R5: No future dates
#     if mark_date > date.today():
#         return None, 'Cannot mark attendance for a future date.'

#     # R5: Limit backfill window
#     if (date.today() - mark_date).days > MAX_BACKFILL_DAYS:
#         return None, (
#             f'Attendance can only be marked up to {MAX_BACKFILL_DAYS} '
#             f'days in the past. Contact HOD for older corrections.'
#         )

#     students = _get_enrolled_students(subject)

#     # Check which students already have a record for this date
#     existing_map = {}    # student_id → Attendance record
#     existing_records = Attendance.query.filter_by(
#         subject_id=subject.id,
#         date=mark_date
#     ).all()
#     for rec in existing_records:
#         existing_map[rec.student_id] = rec

#     already_marked = len(existing_map) > 0

#     # Build per-student data
#     student_rows = []
#     for student in students:
#         existing = existing_map.get(student.id)
#         student_rows.append({
#             'student'        : student,
#             'existing_record': existing,
#             'current_status' : existing.status if existing else 'present',
#             'already_marked' : existing is not None,
#         })

#     return {
#         'subject'       : subject,
#         'teacher'       : teacher,
#         'student_rows'  : student_rows,
#         'mark_date'     : mark_date,
#         'already_marked': already_marked,
#         'valid_statuses': VALID_STATUSES,
#         'status_labels' : STATUS_LABELS,
#         'status_colors' : STATUS_COLORS,
#         'backfill_dates': _get_backfill_date_options(),
#     }, None


# def _get_backfill_date_options():
#     """
#     Returns list of (date, label) tuples for the last 7 days.
#     Used to populate the date picker in the form.
#     """
#     options = []
#     today = date.today()
#     for i in range(MAX_BACKFILL_DAYS + 1):
#         d = today - timedelta(days=i)
#         label = 'Today' if i == 0 else (
#             'Yesterday' if i == 1 else d.strftime('%A, %d %b')
#         )
#         options.append((d, label))
#     return options


# # ══════════════════════════════════════════════════════════════════════
# #  MARK ATTENDANCE
# #  The core write operation.
# # ══════════════════════════════════════════════════════════════════════

# def mark_attendance(teacher_user, subject_id, status_map, mark_date=None):
#     """
#     Mark attendance for a class session.

#     status_map: dict of {student_id (int): status (str)}
#                 Comes from the submitted form.

#     mark_date: date object. Defaults to today.
#                Limited to MAX_BACKFILL_DAYS in the past.

#     DUPLICATE PREVENTION (R1):
#     ──────────────────────────
#     We check for existing records BEFORE inserting.
#     The DB also has a UniqueConstraint as a final safety net.

#     If ALL students already have records for this date → returns
#     a clear error ("Already marked, contact HOD to edit").

#     If SOME students have records (partial, e.g. added mid-day) →
#     inserts for new students only, reports the count.

#     NO EDITS:
#     ─────────
#     If a record already exists for a student on this date,
#     we SKIP it entirely. The teacher cannot overwrite it.
#     Only the HOD can edit via hod_service.

#     Returns: dict with inserted/skipped counts and result details
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return {'error': 'Teacher profile not found.'}

#     subject = Subject.query.get(subject_id)
#     if not subject:
#         return {'error': 'Subject not found.'}

#     # Validate teacher → subject ownership
#     if not teacher_user.is_hod:
#         assigned_ids = [s.id for s in teacher.subjects.all()]
#         if subject.id not in assigned_ids:
#             return {'error': 'You are not assigned to this subject.'}

#     mark_date = mark_date or date.today()

#     # R5: Date validation
#     if mark_date > date.today():
#         return {'error': 'Cannot mark attendance for a future date.'}

#     if (date.today() - mark_date).days > MAX_BACKFILL_DAYS:
#         return {
#             'error': (
#                 f'Attendance can only be marked up to {MAX_BACKFILL_DAYS} '
#                 f'days in the past.'
#             )
#         }

#     # Validate all statuses
#     for student_id, status in status_map.items():
#         if status not in VALID_STATUSES:
#             return {'error': f'Invalid status "{status}". '
#                              f'Allowed: {", ".join(VALID_STATUSES)}.'}

#     # Fetch enrolled students
#     students = _get_enrolled_students(subject)
#     if not students:
#         return {'error': 'No enrolled students found for this subject.'}

#     # Build a set of student IDs that already have records for this date
#     existing_ids = {
#         r.student_id
#         for r in Attendance.query.filter_by(
#             subject_id=subject.id,
#             date=mark_date
#         ).all()
#     }

#     # ALL already marked → complete duplicate
#     if existing_ids and len(existing_ids) >= len(students):
#         return {
#             'error': (
#                 'Attendance for this date has already been fully marked. '
#                 'Only the HOD can edit existing records.'
#             )
#         }

#     inserted = 0
#     skipped  = 0
#     student_ids = {s.id for s in students}

#     for student in students:
#         # R1: Skip if already has a record
#         if student.id in existing_ids:
#             skipped += 1
#             continue

#         status = status_map.get(student.id, 'absent')
#         if status not in VALID_STATUSES:
#             status = 'absent'    # safe fallback

#         db.session.add(Attendance(
#             student_id   = student.id,
#             subject_id   = subject.id,
#             marked_by_id = teacher.id,
#             date         = mark_date,
#             status       = status,
#             semester     = student.semester
#         ))
#         inserted += 1

#     if inserted:
#         # Update total_classes on the subject for tracking
#         # We only count non-leave/non-event days as a class conducted
#         statuses_given = list(status_map.values())
#         if any(s not in ('leave', 'event') for s in statuses_given):
#             subject.total_classes = (
#                 Attendance.query
#                 .filter_by(subject_id=subject.id)
#                 .filter(Attendance.status.notin_(['leave', 'event']))
#                 .distinct(Attendance.date)
#                 .count()
#             ) + 1  # +1 for today (not yet committed)

#         db.session.commit()

#     return {
#         'inserted': inserted,
#         'skipped' : skipped,
#         'date'    : mark_date,
#         'subject' : subject.name,
#         'message' : (
#             f'Attendance saved for {inserted} student(s) on '
#             f'{mark_date.strftime("%d %b %Y")}.'
#             + (f' {skipped} skipped (already marked).' if skipped else '')
#         )
#     }


# # ══════════════════════════════════════════════════════════════════════
# #  ATTENDANCE HISTORY
# # ══════════════════════════════════════════════════════════════════════

# def get_subject_attendance_history(teacher_user, subject_id, limit=30):
#     """
#     Return recent attendance sessions for a subject.
#     Grouped by date — each date shows all student records for that class.

#     limit: number of distinct dates to return (most recent first).
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return []

#     subject = Subject.query.get(subject_id)
#     if not subject:
#         return []

#     # Get distinct dates this subject had attendance
#     from sqlalchemy import distinct, desc
#     dates = (
#         db.session.query(distinct(Attendance.date))
#         .filter_by(subject_id=subject.id)
#         .order_by(desc(Attendance.date))
#         .limit(limit)
#         .all()
#     )

#     history = []
#     for (att_date,) in dates:
#         records = Attendance.query.filter_by(
#             subject_id=subject.id,
#             date=att_date
#         ).order_by(Attendance.student_id).all()

#         present  = sum(1 for r in records if r.status == 'present')
#         absent   = sum(1 for r in records if r.status == 'absent')
#         on_leave = sum(1 for r in records if r.status == 'leave')
#         on_event = sum(1 for r in records if r.status == 'event')
#         total    = len(records)

#         history.append({
#             'date'    : att_date,
#             'records' : records,
#             'present' : present,
#             'absent'  : absent,
#             'leave'   : on_leave,
#             'event'   : on_event,
#             'total'   : total,
#             'pct'     : round(present / (total - on_leave - on_event) * 100, 1)
#                         if (total - on_leave - on_event) > 0 else 0.0,
#         })

#     return history


# def get_student_subject_attendance(subject_id, student_id):
#     """
#     Get all attendance records for ONE student in ONE subject.
#     Used to show a student's per-subject history.
#     """
#     return (
#         Attendance.query
#         .filter_by(subject_id=subject_id, student_id=student_id)
#         .order_by(Attendance.date.desc())
#         .all()
#     )

#############-----------------------updated----------------
"""
TEACHER SERVICE
===============
Business logic for the teacher dashboard.

Covers:
  1. Dashboard data — subjects, today's status, stats
  2. Attendance marking — insert-only, no edits, duplicate prevention
  3. Attendance history — what was marked on each date
  4. Student roster — who is enrolled in a subject's semester

CORE RULES enforced here:
  R1. ONE record per student per subject per day (DB unique constraint +
      service-level check)
  R2. Teacher can only mark attendance for subjects ASSIGNED to them
      (enforced by @teacher_owns_subject decorator + service ownership check)
  R3. Teacher CANNOT edit any existing attendance record — attempt returns error
  R4. 'leave' and 'event' statuses do NOT affect attendance percentage
  R5. A teacher can mark attendance for a past date (if they forgot)
      but not for a future date
"""

from datetime import date, datetime, timedelta
from app import db
from app.models.attendance import Attendance
from app.models.student    import Student
from app.models.subject    import Subject
from app.models.teacher    import Teacher
from app.models.user       import User


# ══════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════

VALID_STATUSES = ('present', 'absent', 'leave', 'event')

STATUS_LABELS = {
    'present': 'Present',
    'absent' : 'Absent',
    'leave'  : 'Leave',
    'event'  : 'Event / Duty',
}

STATUS_COLORS = {
    'present': 'success',
    'absent' : 'danger',
    'leave'  : 'warning',
    'event'  : 'info',
}

# How many past days a teacher can backfill attendance for
MAX_BACKFILL_DAYS = 7


# ══════════════════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════════════════

def _get_teacher(teacher_user):
    """Get the Teacher profile for the logged-in user."""
    return Teacher.query.filter_by(user_id=teacher_user.id).first()


def _get_enrolled_students(subject):
    """
    Return all active non-graduated students who are enrolled in
    the semester/program/department that this subject belongs to.
    """
    return (
        Student.query
        .filter_by(
            department_id = subject.department_id,
            semester      = subject.semester,
            program_type  = subject.program_type,
            is_graduated  = False,
        )
        .join(Student.user)
        .filter(User.is_active == True)
        .order_by(Student.roll_number)
        .all()
    )


# ══════════════════════════════════════════════════════════════════════
#  DASHBOARD DATA
# ══════════════════════════════════════════════════════════════════════

def get_teacher_dashboard_data(teacher_user):
    """
    Aggregates everything the teacher dashboard needs in one call.

    Returns a dict with:
      - teacher profile
      - their subjects with today's marking status
      - recent attendance activity
      - subject-level stats
    """
    teacher = _get_teacher(teacher_user)
    if not teacher:
        return {'error': 'Teacher profile not found.'}

    today = date.today()
    subjects_data = []

    for subject in teacher.subjects.order_by(Subject.semester, Subject.name).all():
        students      = _get_enrolled_students(subject)
        total_students = len(students)

        # Check if attendance was already marked today for this subject
        today_records = Attendance.query.filter_by(
            subject_id=subject.id,
            date=today
        ).count()

        already_marked_today = today_records > 0

        # Overall subject attendance stats
        all_records = subject.attendance_records.all()
        conducted   = [r for r in all_records if r.status not in ('leave', 'event')]
        present     = [r for r in conducted    if r.status == 'present']

        subjects_data.append({
            'subject'             : subject,
            'total_students'      : total_students,
            'already_marked_today': already_marked_today,
            'today_marked_count'  : today_records,
            'total_conducted'     : len(conducted),
            'avg_attendance_pct'  : (
                round(len(present) / len(conducted) * 100, 1)
                if conducted else 0.0
            ),
        })

    return {
        'teacher'      : teacher,
        'subjects_data': subjects_data,
        'today'        : today,
        'dept_name'    : teacher.department.name,
        'dept_code'    : teacher.department.code,
    }


# ══════════════════════════════════════════════════════════════════════
#  ATTENDANCE SESSION SETUP
#  Prepares everything the mark-attendance form needs.
# ══════════════════════════════════════════════════════════════════════

def get_attendance_session(teacher_user, subject_id, for_date=None):
    """
    Prepare the data needed to show the mark-attendance form.

    for_date: date object (defaults to today).
              Teachers can submit for a past date (backfill window).

    Returns a dict containing:
      - subject
      - students list with their current attendance status for this date
      - whether this session already has records (already_marked)
      - the date we're marking for
      - valid statuses for the dropdown
    """
    teacher = _get_teacher(teacher_user)
    if not teacher:
        return None, 'Teacher profile not found.'

    subject = Subject.query.get(subject_id)
    if not subject:
        return None, 'Subject not found.'

    # Validate teacher owns this subject (HODs bypass this check)
    if not teacher_user.is_hod:
        assigned_ids = [s.id for s in teacher.subjects.all()]
        if subject.id not in assigned_ids:
            return None, 'You are not assigned to teach this subject.'

    mark_date = for_date or date.today()

    # R5: No future dates
    if mark_date > date.today():
        return None, 'Cannot mark attendance for a future date.'

    # R5: Limit backfill window
    if (date.today() - mark_date).days > MAX_BACKFILL_DAYS:
        return None, (
            f'Attendance can only be marked up to {MAX_BACKFILL_DAYS} '
            f'days in the past. Contact HOD for older corrections.'
        )

    students = _get_enrolled_students(subject)

    # Check which students already have a record for this date
    existing_map = {}    # student_id → Attendance record
    existing_records = Attendance.query.filter_by(
        subject_id=subject.id,
        date=mark_date
    ).all()
    for rec in existing_records:
        existing_map[rec.student_id] = rec

    already_marked = len(existing_map) > 0

    # Build per-student data
    student_rows = []
    for student in students:
        existing = existing_map.get(student.id)
        student_rows.append({
            'student'        : student,
            'existing_record': existing,
            'current_status' : existing.status if existing else 'present',
            'already_marked' : existing is not None,
        })

    return {
        'subject'       : subject,
        'teacher'       : teacher,
        'student_rows'  : student_rows,
        'mark_date'     : mark_date,
        'already_marked': already_marked,
        'valid_statuses': VALID_STATUSES,
        'status_labels' : STATUS_LABELS,
        'status_colors' : STATUS_COLORS,
        'backfill_dates': _get_backfill_date_options(),
    }, None


def _get_backfill_date_options():
    """
    Returns list of (date, label) tuples for the last 7 days.
    Used to populate the date picker in the form.
    """
    options = []
    today = date.today()
    for i in range(MAX_BACKFILL_DAYS + 1):
        d = today - timedelta(days=i)
        label = 'Today' if i == 0 else (
            'Yesterday' if i == 1 else d.strftime('%A, %d %b')
        )
        options.append((d, label))
    return options


# ══════════════════════════════════════════════════════════════════════
#  MARK ATTENDANCE
#  The core write operation.
# ══════════════════════════════════════════════════════════════════════

def mark_attendance(teacher_user, subject_id, status_map, mark_date=None):
    """
    Mark attendance for a class session.

    status_map: dict of {student_id (int): status (str)}
                Comes from the submitted form.

    mark_date: date object. Defaults to today.
               Limited to MAX_BACKFILL_DAYS in the past.

    DUPLICATE PREVENTION (R1):
    ──────────────────────────
    We check for existing records BEFORE inserting.
    The DB also has a UniqueConstraint as a final safety net.

    If ALL students already have records for this date → returns
    a clear error ("Already marked, contact HOD to edit").

    If SOME students have records (partial, e.g. added mid-day) →
    inserts for new students only, reports the count.

    NO EDITS:
    ─────────
    If a record already exists for a student on this date,
    we SKIP it entirely. The teacher cannot overwrite it.
    Only the HOD can edit via hod_service.

    Returns: dict with inserted/skipped counts and result details
    """
    teacher = _get_teacher(teacher_user)
    if not teacher:
        return {'error': 'Teacher profile not found.'}

    subject = Subject.query.get(subject_id)
    if not subject:
        return {'error': 'Subject not found.'}

    # Validate teacher → subject ownership
    if not teacher_user.is_hod:
        assigned_ids = [s.id for s in teacher.subjects.all()]
        if subject.id not in assigned_ids:
            return {'error': 'You are not assigned to this subject.'}

    mark_date = mark_date or date.today()

    # R5: Date validation
    if mark_date > date.today():
        return {'error': 'Cannot mark attendance for a future date.'}

    if (date.today() - mark_date).days > MAX_BACKFILL_DAYS:
        return {
            'error': (
                f'Attendance can only be marked up to {MAX_BACKFILL_DAYS} '
                f'days in the past.'
            )
        }

    # Validate all statuses
    for student_id, status in status_map.items():
        if status not in VALID_STATUSES:
            return {'error': f'Invalid status "{status}". '
                             f'Allowed: {", ".join(VALID_STATUSES)}.'}

    # Fetch enrolled students
    students = _get_enrolled_students(subject)
    if not students:
        return {'error': 'No enrolled students found for this subject.'}

    # Build a set of student IDs that already have records for this date
    existing_ids = {
        r.student_id
        for r in Attendance.query.filter_by(
            subject_id=subject.id,
            date=mark_date
        ).all()
    }

    # ALL already marked → complete duplicate
    if existing_ids and len(existing_ids) >= len(students):
        return {
            'error': (
                'Attendance for this date has already been fully marked. '
                'Only the HOD can edit existing records.'
            )
        }

    inserted = 0
    skipped  = 0
    student_ids = {s.id for s in students}

    for student in students:
        # R1: Skip if already has a record
        if student.id in existing_ids:
            skipped += 1
            continue

        status = status_map.get(student.id, 'absent')
        if status not in VALID_STATUSES:
            status = 'absent'    # safe fallback

        db.session.add(Attendance(
            student_id   = student.id,
            subject_id   = subject.id,
            marked_by_id = teacher.id,
            date         = mark_date,
            status       = status,
            semester     = student.semester
        ))
        inserted += 1

    if inserted:
        # Update total_classes on the subject for tracking
        statuses_given = list(status_map.values())
        if any(s not in ('leave', 'event') for s in statuses_given):
            subject.total_classes = (
                Attendance.query
                .filter_by(subject_id=subject.id)
                .filter(Attendance.status.notin_(['leave', 'event']))
                .distinct(Attendance.date)
                .count()
            ) + 1  # +1 for today (not yet committed)

        db.session.commit()

        # After marking, check each affected student for low attendance
        # and send a notification if they've dropped below 75%
        from app.services.student_service import check_and_notify_low_attendance
        for student in students:
            if student.id in status_map:
                check_and_notify_low_attendance(student.id)

    return {
        'inserted': inserted,
        'skipped' : skipped,
        'date'    : mark_date,
        'subject' : subject.name,
        'message' : (
            f'Attendance saved for {inserted} student(s) on '
            f'{mark_date.strftime("%d %b %Y")}.'
            + (f' {skipped} skipped (already marked).' if skipped else '')
        )
    }


# ══════════════════════════════════════════════════════════════════════
#  ATTENDANCE HISTORY
# ══════════════════════════════════════════════════════════════════════

def get_subject_attendance_history(teacher_user, subject_id, limit=30):
    """
    Return recent attendance sessions for a subject.
    Grouped by date — each date shows all student records for that class.

    limit: number of distinct dates to return (most recent first).
    """
    teacher = _get_teacher(teacher_user)
    if not teacher:
        return []

    subject = Subject.query.get(subject_id)
    if not subject:
        return []

    # Get distinct dates this subject had attendance
    from sqlalchemy import distinct, desc
    dates = (
        db.session.query(distinct(Attendance.date))
        .filter_by(subject_id=subject.id)
        .order_by(desc(Attendance.date))
        .limit(limit)
        .all()
    )

    history = []
    for (att_date,) in dates:
        records = Attendance.query.filter_by(
            subject_id=subject.id,
            date=att_date
        ).order_by(Attendance.student_id).all()

        present  = sum(1 for r in records if r.status == 'present')
        absent   = sum(1 for r in records if r.status == 'absent')
        on_leave = sum(1 for r in records if r.status == 'leave')
        on_event = sum(1 for r in records if r.status == 'event')
        total    = len(records)

        history.append({
            'date'    : att_date,
            'records' : records,
            'present' : present,
            'absent'  : absent,
            'leave'   : on_leave,
            'event'   : on_event,
            'total'   : total,
            'pct'     : round(present / (total - on_leave - on_event) * 100, 1)
                        if (total - on_leave - on_event) > 0 else 0.0,
        })

    return history


def get_student_subject_attendance(subject_id, student_id):
    """
    Get all attendance records for ONE student in ONE subject.
    Used to show a student's per-subject history.
    """
    return (
        Attendance.query
        .filter_by(subject_id=subject_id, student_id=student_id)
        .order_by(Attendance.date.desc())
        .all()
    )
