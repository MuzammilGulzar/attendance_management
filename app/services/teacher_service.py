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

#############---------fix minor bugs------------
# """
# TEACHER SERVICE
# ===============
# Business logic for the teacher dashboard.

# Covers:
#   1. Dashboard data — subjects, today's status, pending QR count
#   2. Attendance marking — insert-only, no edits, duplicate prevention
#   3. Attendance history — what was marked on each date
#   4. Student roster — who is enrolled in a subject's semester
#   5. QR Review — get pending submissions, confirm final statuses

# CORE RULES enforced here:
#   R1. ONE record per student per subject per day (DB unique constraint +
#       service-level check)
#   R2. Teacher can only mark attendance for subjects ASSIGNED to them
#   R3. Teacher CANNOT edit any existing finalised attendance record
#   R4. 'leave', 'event', 'no_class', 'pending' do NOT affect attendance %
#   R5. A teacher can mark attendance for a past date (backfill window)
#       but not for a future date
#   R6. Only the teacher who owns the subject can review its QR submissions
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

# # Statuses a teacher can use during MANUAL attendance marking.
# # Does not include 'pending' (QR-only) but includes 'no_class'.
# VALID_STATUSES = ('present', 'absent', 'leave', 'event', 'no_class')

# # Statuses a teacher can assign during QR REVIEW.
# # Excludes 'absent' — unscanned students stay absent by default
# # (the service handles that). Excludes 'pending' — that's the
# # source state, not a target.
# REVIEW_STATUSES = ('present', 'leave', 'event', 'no_class')

# STATUS_LABELS = {
#     'present' : 'Present',
#     'absent'  : 'Absent',
#     'leave'   : 'Leave',
#     'event'   : 'Event / Duty',
#     'no_class': 'No Class / Holiday',
#     'pending' : 'Pending Review',
# }

# STATUS_COLORS = {
#     'present' : 'success',
#     'absent'  : 'danger',
#     'leave'   : 'warning',
#     'event'   : 'info',
#     'no_class': 'secondary',
#     'pending' : 'primary',
# }

# MAX_BACKFILL_DAYS = 7


# # ══════════════════════════════════════════════════════════════════════
# #  HELPERS
# # ══════════════════════════════════════════════════════════════════════

# def _get_teacher(teacher_user):
#     """Get the Teacher profile for the logged-in user."""
#     return Teacher.query.filter_by(user_id=teacher_user.id).first()


# def _get_enrolled_students(subject):
#     """
#     Return all active non-graduated students enrolled in
#     this subject's semester/program/department.
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
#       teacher       → Teacher object
#       subjects_data → list of per-subject dicts
#       today         → date.today()
#       dept_name     → department name
#       dept_code     → department code
#       pending_total → total pending QR submissions across all subjects
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return {'error': 'Teacher profile not found.'}

#     today         = date.today()
#     subjects_data = []
#     pending_total = 0

#     for subject in teacher.subjects.order_by(Subject.semester, Subject.name).all():
#         students       = _get_enrolled_students(subject)
#         total_students = len(students)

#         today_records = Attendance.query.filter_by(
#             subject_id=subject.id,
#             date=today
#         ).count()

#         already_marked_today = today_records > 0

#         # Pending QR submissions for this subject (any date)
#         pending_count = Attendance.query.filter_by(
#             subject_id = subject.id,
#             status     = 'pending',
#         ).count()
#         pending_total += pending_count

#         # Overall subject attendance stats
#         # Only count present and absent as "conducted"
#         all_records = subject.attendance_records.all()
#         conducted   = [r for r in all_records
#                        if r.status in ('present', 'absent')]
#         present     = [r for r in conducted if r.status == 'present']

#         subjects_data.append({
#             'subject'             : subject,
#             'total_students'      : total_students,
#             'already_marked_today': already_marked_today,
#             'today_marked_count'  : today_records,
#             'pending_count'       : pending_count,
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
#         'pending_total': pending_total,
#     }


# # ══════════════════════════════════════════════════════════════════════
# #  ATTENDANCE SESSION SETUP
# # ══════════════════════════════════════════════════════════════════════

# def get_attendance_session(teacher_user, subject_id, for_date=None):
#     """
#     Prepare data for the mark-attendance form.

#     Returns (session_dict, None) on success
#             (None, error_str) on failure
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return None, 'Teacher profile not found.'

#     subject = Subject.query.get(subject_id)
#     if not subject:
#         return None, 'Subject not found.'

#     if not teacher_user.is_hod:
#         assigned_ids = [s.id for s in teacher.subjects.all()]
#         if subject.id not in assigned_ids:
#             return None, 'You are not assigned to teach this subject.'

#     mark_date = for_date or date.today()

#     if mark_date > date.today():
#         return None, 'Cannot mark attendance for a future date.'

#     if (date.today() - mark_date).days > MAX_BACKFILL_DAYS:
#         return None, (
#             f'Attendance can only be marked up to {MAX_BACKFILL_DAYS} '
#             f'days in the past. Contact HOD for older corrections.'
#         )

#     students = _get_enrolled_students(subject)

#     existing_map = {}
#     for rec in Attendance.query.filter_by(
#         subject_id=subject.id, date=mark_date
#     ).all():
#         existing_map[rec.student_id] = rec

#     already_marked = len(existing_map) > 0

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
#     """(date, label) tuples for the last MAX_BACKFILL_DAYS days."""
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
# #  MARK ATTENDANCE  (manual — teacher form)
# # ══════════════════════════════════════════════════════════════════════

# def mark_attendance(teacher_user, subject_id, status_map, mark_date=None):
#     """
#     Mark attendance for a class session.

#     status_map: {student_id (int): status (str)}

#     VALID_STATUSES for manual marking: present, absent, leave, event, no_class
#     (pending is excluded — it is QR-only and set by qr_service)

#     Returns dict with inserted/skipped counts and a message.
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return {'error': 'Teacher profile not found.'}

#     subject = Subject.query.get(subject_id)
#     if not subject:
#         return {'error': 'Subject not found.'}

#     if not teacher_user.is_hod:
#         assigned_ids = [s.id for s in teacher.subjects.all()]
#         if subject.id not in assigned_ids:
#             return {'error': 'You are not assigned to this subject.'}

#     mark_date = mark_date or date.today()

#     if mark_date > date.today():
#         return {'error': 'Cannot mark attendance for a future date.'}

#     if (date.today() - mark_date).days > MAX_BACKFILL_DAYS:
#         return {
#             'error': (
#                 f'Attendance can only be marked up to {MAX_BACKFILL_DAYS} '
#                 f'days in the past.'
#             )
#         }

#     # Validate all statuses — only VALID_STATUSES allowed here (not pending)
#     for student_id, status in status_map.items():
#         if status not in VALID_STATUSES:
#             return {'error': f'Invalid status "{status}". '
#                              f'Allowed: {", ".join(VALID_STATUSES)}.'}

#     students = _get_enrolled_students(subject)
#     if not students:
#         return {'error': 'No enrolled students found for this subject.'}

#     existing_ids = {
#         r.student_id
#         for r in Attendance.query.filter_by(
#             subject_id=subject.id,
#             date=mark_date
#         ).all()
#     }

#     if existing_ids and len(existing_ids) >= len(students):
#         return {
#             'error': (
#                 'Attendance for this date has already been fully marked. '
#                 'Only the HOD can edit existing records.'
#             )
#         }

#     inserted = 0
#     skipped  = 0

#     for student in students:
#         if student.id in existing_ids:
#             skipped += 1
#             continue

#         status = status_map.get(student.id, 'absent')
#         if status not in VALID_STATUSES:
#             status = 'absent'

#         db.session.add(Attendance(
#             student_id   = student.id,
#             subject_id   = subject.id,
#             marked_by_id = teacher.id,
#             date         = mark_date,
#             status       = status,
#             semester     = student.semester,
#             is_qr_scan   = False,
#         ))
#         inserted += 1

#     if inserted:
#         # Only count non-neutral dates toward total_classes
#         neutral = ('leave', 'event', 'no_class', 'pending')
#         statuses_given = list(status_map.values())
#         if any(s not in neutral for s in statuses_given):
#             subject.total_classes = (
#                 Attendance.query
#                 .filter_by(subject_id=subject.id)
#                 .filter(Attendance.status.notin_(list(neutral)))
#                 .distinct(Attendance.date)
#                 .count()
#             ) + 1

#         db.session.commit()

#         from app.services.student_service import check_and_notify_low_attendance
#         for student in students:
#             if student.id in status_map:
#                 check_and_notify_low_attendance(student.id)

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
# #  QR REVIEW  (NEW — Step 3)
# # ══════════════════════════════════════════════════════════════════════

# def get_pending_qr_submissions(teacher_user, subject_id):
#     """
#     Return all pending QR submissions for a subject, grouped by date.

#     Called by: GET /teacher/review-qr/<subject_id>

#     Only returns records where:
#       - is_qr_scan = True        (created by a student scan)
#       - status     = 'pending'   (not yet reviewed by teacher)

#     Grouped by date so the teacher sees one block per class session.

#     Returns a list of dicts:
#       [
#         {
#           'date'    : date,
#           'records' : [Attendance, ...],   pending records for that date
#           'count'   : int,
#         },
#         ...
#       ]
#     Ordered newest date first.
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return []

#     subject = Subject.query.get(subject_id)
#     if not subject:
#         return []

#     # Security: teacher must own this subject
#     if not teacher_user.is_hod:
#         assigned_ids = [s.id for s in teacher.subjects.all()]
#         if subject.id not in assigned_ids:
#             return []

#     pending_records = (
#         Attendance.query
#         .filter_by(
#             subject_id = subject.id,
#             status     = 'pending',
#             is_qr_scan = True,
#         )
#         .order_by(Attendance.date.desc(), Attendance.student_id)
#         .all()
#     )

#     # Group by date
#     from collections import defaultdict
#     by_date = defaultdict(list)
#     for rec in pending_records:
#         by_date[rec.date].append(rec)

#     result = []
#     for att_date in sorted(by_date.keys(), reverse=True):
#         recs = by_date[att_date]
#         result.append({
#             'date'   : att_date,
#             'records': recs,
#             'count'  : len(recs),
#         })

#     return result


# def review_qr_submissions(teacher_user, subject_id, review_date, status_map):
#     """
#     Teacher confirms QR scan submissions for a specific date.

#     Called by: POST /teacher/review-qr/<subject_id>

#     HOW IT WORKS:
#     ─────────────
#     status_map: {attendance_id (int): new_status (str)}
#       The form sends one status per pending record.
#       new_status must be one of REVIEW_STATUSES:
#         'present', 'leave', 'event', 'no_class'

#     For each pending record in status_map:
#       - Validate the new_status
#       - Call record.apply_teacher_review() to set status + reviewer
#       - Mark record as no longer pending

#     After reviewing, also mark ALL ENROLLED STUDENTS who did NOT scan
#     as 'absent' for that date (if they have no record yet).
#     This completes the session — every student ends up with a record.

#     Parameters:
#       teacher_user  → User object of the reviewing teacher
#       subject_id    → Subject.id
#       review_date   → date object — which day's submissions to review
#       status_map    → {attendance_id: new_status}

#     Returns: (True, summary_dict) on success
#              (False, error_str)   on failure

#     summary_dict contains:
#       reviewed    → how many pending records were confirmed
#       auto_absent → how many absent records were auto-created
#       message     → human-readable summary
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return False, 'Teacher profile not found.'

#     subject = Subject.query.get(subject_id)
#     if not subject:
#         return False, 'Subject not found.'

#     # Security check
#     if not teacher_user.is_hod:
#         assigned_ids = [s.id for s in teacher.subjects.all()]
#         if subject.id not in assigned_ids:
#             return False, 'You are not assigned to this subject.'

#     if not status_map:
#         return False, 'No review data submitted.'

#     # Validate all incoming statuses before writing anything
#     for att_id, new_status in status_map.items():
#         if new_status not in REVIEW_STATUSES:
#             return False, (
#                 f'Invalid status "{new_status}". '
#                 f'Allowed during review: {", ".join(REVIEW_STATUSES)}.'
#             )

#     # Fetch and confirm pending records
#     reviewed = 0
#     for att_id, new_status in status_map.items():
#         record = Attendance.query.get(att_id)
#         if not record:
#             continue
#         if record.subject_id != subject.id:
#             continue   # security — can't review another subject's records
#         if record.status != 'pending':
#             continue   # already reviewed — skip silently

#         record.apply_teacher_review(new_status, teacher)
#         reviewed += 1

#     # Auto-mark absent for enrolled students who didn't scan
#     # This ensures every enrolled student has a record for this date
#     enrolled_students = _get_enrolled_students(subject)
#     already_have_record = {
#         r.student_id
#         for r in Attendance.query.filter_by(
#             subject_id = subject.id,
#             date       = review_date,
#         ).all()
#     }

#     auto_absent = 0
#     for student in enrolled_students:
#         if student.id not in already_have_record:
#             db.session.add(Attendance(
#                 student_id   = student.id,
#                 subject_id   = subject.id,
#                 marked_by_id = teacher.id,
#                 date         = review_date,
#                 status       = 'absent',
#                 semester     = student.semester,
#                 is_qr_scan   = False,
#             ))
#             auto_absent += 1

#     db.session.commit()

#     # Check low attendance for all affected students
#     from app.services.student_service import check_and_notify_low_attendance
#     for student in enrolled_students:
#         check_and_notify_low_attendance(student.id)

#     message = (
#         f'Review complete for {review_date.strftime("%d %b %Y")}: '
#         f'{reviewed} QR submission(s) confirmed, '
#         f'{auto_absent} student(s) auto-marked absent.'
#     )

#     return True, {
#         'reviewed'   : reviewed,
#         'auto_absent': auto_absent,
#         'message'    : message,
#     }


# # ══════════════════════════════════════════════════════════════════════
# #  ATTENDANCE HISTORY
# # ══════════════════════════════════════════════════════════════════════

# def get_subject_attendance_history(teacher_user, subject_id, limit=30):
#     """
#     Return recent attendance sessions for a subject, grouped by date.
#     """
#     teacher = _get_teacher(teacher_user)
#     if not teacher:
#         return []

#     subject = Subject.query.get(subject_id)
#     if not subject:
#         return []

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
#         no_class = sum(1 for r in records if r.status == 'no_class')
#         pending  = sum(1 for r in records if r.status == 'pending')
#         conducted = present + absent   # only present+absent count

#         history.append({
#             'date'    : att_date,
#             'records' : records,
#             'present' : present,
#             'absent'  : absent,
#             'leave'   : on_leave,
#             'event'   : on_event,
#             'no_class': no_class,
#             'pending' : pending,
#             'total'   : len(records),
#             'pct'     : round(present / conducted * 100, 1)
#                         if conducted > 0 else 0.0,
#         })

#     return history


# def get_student_subject_attendance(subject_id, student_id):
#     """
#     All attendance records for ONE student in ONE subject.
#     """
#     return (
#         Attendance.query
#         .filter_by(subject_id=subject_id, student_id=student_id)
#         .order_by(Attendance.date.desc())
#         .all()
#     )


######################
#____________________
#################
"""
TEACHER SERVICE
===============
Business logic for the teacher dashboard.

Covers:
  1. Dashboard data — subjects, today's status, pending QR count
  2. Attendance marking — insert-only, no edits, duplicate prevention
  3. Attendance history — what was marked on each date
  4. Student roster — who is enrolled in a subject's semester
  5. QR Review — get pending submissions, confirm final statuses

CORE RULES enforced here:
  R1. ONE record per student per subject per day (DB unique constraint +
      service-level check)
  R2. Teacher can only mark attendance for subjects ASSIGNED to them
  R3. Teacher CANNOT edit any existing finalised attendance record
  R4. 'leave', 'event', 'no_class', 'pending' do NOT affect attendance %
  R5. A teacher can mark attendance for a past date (backfill window)
      but not for a future date
  R6. Only the teacher who owns the subject can review its QR submissions
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

# Statuses a teacher can use during MANUAL attendance marking.
# Does not include 'pending' (QR-only) but includes 'no_class'.
VALID_STATUSES = ('present', 'absent', 'leave', 'event', 'no_class')

# Statuses a teacher can assign during QR REVIEW.
# Excludes 'absent' — unscanned students stay absent by default
# (the service handles that). Excludes 'pending' — that's the
# source state, not a target.
REVIEW_STATUSES = ('present', 'leave', 'event', 'no_class')

STATUS_LABELS = {
    'present' : 'Present',
    'absent'  : 'Absent',
    'leave'   : 'Leave',
    'event'   : 'Event / Duty',
    'no_class': 'No Class / Holiday',
    'pending' : 'Pending Review',
}

STATUS_COLORS = {
    'present' : 'success',
    'absent'  : 'danger',
    'leave'   : 'warning',
    'event'   : 'info',
    'no_class': 'secondary',
    'pending' : 'primary',
}

MAX_BACKFILL_DAYS = 7


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════

def _get_teacher(teacher_user):
    """Get the Teacher profile for the logged-in user."""
    return Teacher.query.filter_by(user_id=teacher_user.id).first()


def _get_enrolled_students(subject):
    """
    Return all active non-graduated students enrolled in
    this subject's semester/program/department.
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
      teacher       → Teacher object
      subjects_data → list of per-subject dicts
      today         → date.today()
      dept_name     → department name
      dept_code     → department code
      pending_total → total pending QR submissions across all subjects
    """
    teacher = _get_teacher(teacher_user)
    if not teacher:
        return {'error': 'Teacher profile not found.'}

    today         = date.today()
    subjects_data = []
    pending_total = 0

    for subject in teacher.subjects.order_by(Subject.semester, Subject.name).all():
        students       = _get_enrolled_students(subject)
        total_students = len(students)

        today_records = Attendance.query.filter_by(
            subject_id=subject.id,
            date=today
        ).count()

        already_marked_today = today_records > 0

        # Pending QR submissions for this subject (any date)
        pending_count = Attendance.query.filter_by(
            subject_id = subject.id,
            status     = 'pending',
        ).count()
        pending_total += pending_count

        # Overall subject attendance stats
        # Only count present and absent as "conducted"
        all_records = subject.attendance_records.all()
        conducted   = [r for r in all_records
                       if r.status in ('present', 'absent')]
        present     = [r for r in conducted if r.status == 'present']

        subjects_data.append({
            'subject'             : subject,
            'total_students'      : total_students,
            'already_marked_today': already_marked_today,
            'today_marked_count'  : today_records,
            'pending_count'       : pending_count,
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
        'pending_total': pending_total,
    }


# ══════════════════════════════════════════════════════════════════════
#  ATTENDANCE SESSION SETUP
# ══════════════════════════════════════════════════════════════════════

def get_attendance_session(teacher_user, subject_id, for_date=None):
    """
    Prepare data for the mark-attendance form.

    Returns (session_dict, None) on success
            (None, error_str) on failure
    """
    teacher = _get_teacher(teacher_user)
    if not teacher:
        return None, 'Teacher profile not found.'

    subject = Subject.query.get(subject_id)
    if not subject:
        return None, 'Subject not found.'

    if not teacher_user.is_hod:
        assigned_ids = [s.id for s in teacher.subjects.all()]
        if subject.id not in assigned_ids:
            return None, 'You are not assigned to teach this subject.'

    mark_date = for_date or date.today()

    if mark_date > date.today():
        return None, 'Cannot mark attendance for a future date.'

    if (date.today() - mark_date).days > MAX_BACKFILL_DAYS:
        return None, (
            f'Attendance can only be marked up to {MAX_BACKFILL_DAYS} '
            f'days in the past. Contact HOD for older corrections.'
        )

    students = _get_enrolled_students(subject)

    existing_map = {}
    for rec in Attendance.query.filter_by(
        subject_id=subject.id, date=mark_date
    ).all():
        existing_map[rec.student_id] = rec

    already_marked = len(existing_map) > 0

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
    """(date, label) tuples for the last MAX_BACKFILL_DAYS days."""
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
#  MARK ATTENDANCE  (manual — teacher form)
# ══════════════════════════════════════════════════════════════════════

def mark_attendance(teacher_user, subject_id, status_map, mark_date=None):
    """
    Mark attendance for a class session.

    status_map: {student_id (int): status (str)}

    VALID_STATUSES for manual marking: present, absent, leave, event, no_class
    (pending is excluded — it is QR-only and set by qr_service)

    Returns dict with inserted/skipped counts and a message.
    """
    teacher = _get_teacher(teacher_user)
    if not teacher:
        return {'error': 'Teacher profile not found.'}

    subject = Subject.query.get(subject_id)
    if not subject:
        return {'error': 'Subject not found.'}

    if not teacher_user.is_hod:
        assigned_ids = [s.id for s in teacher.subjects.all()]
        if subject.id not in assigned_ids:
            return {'error': 'You are not assigned to this subject.'}

    mark_date = mark_date or date.today()

    if mark_date > date.today():
        return {'error': 'Cannot mark attendance for a future date.'}

    if (date.today() - mark_date).days > MAX_BACKFILL_DAYS:
        return {
            'error': (
                f'Attendance can only be marked up to {MAX_BACKFILL_DAYS} '
                f'days in the past.'
            )
        }

    # Validate all statuses — only VALID_STATUSES allowed here (not pending)
    for student_id, status in status_map.items():
        if status not in VALID_STATUSES:
            return {'error': f'Invalid status "{status}". '
                             f'Allowed: {", ".join(VALID_STATUSES)}.'}

    students = _get_enrolled_students(subject)
    if not students:
        return {'error': 'No enrolled students found for this subject.'}

    existing_ids = {
        r.student_id
        for r in Attendance.query.filter_by(
            subject_id=subject.id,
            date=mark_date
        ).all()
    }

    if existing_ids and len(existing_ids) >= len(students):
        return {
            'error': (
                'Attendance for this date has already been fully marked. '
                'Only the HOD can edit existing records.'
            )
        }

    inserted = 0
    skipped  = 0

    for student in students:
        if student.id in existing_ids:
            skipped += 1
            continue

        status = status_map.get(student.id, 'absent')
        if status not in VALID_STATUSES:
            status = 'absent'

        db.session.add(Attendance(
            student_id   = student.id,
            subject_id   = subject.id,
            marked_by_id = teacher.id,
            date         = mark_date,
            status       = status,
            semester     = student.semester,
            is_qr_scan   = False,
        ))
        inserted += 1

    if inserted:
        # Only count non-neutral dates toward total_classes
        neutral = ('leave', 'event', 'no_class', 'pending')
        statuses_given = list(status_map.values())
        if any(s not in neutral for s in statuses_given):
            subject.total_classes = (
                Attendance.query
                .filter_by(subject_id=subject.id)
                .filter(Attendance.status.notin_(list(neutral)))
                .distinct(Attendance.date)
                .count()
            ) + 1

        db.session.commit()

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
#  QR REVIEW  (NEW — Step 3)
# ══════════════════════════════════════════════════════════════════════

def get_pending_qr_submissions(teacher_user, subject_id):
    """
    Return ALL enrolled students for each QR session date, grouped by date.

    Called by: GET /teacher/review-qr/<subject_id>

    Each group contains TWO lists:
      scanned     → students who scanned the QR (status='pending')
      not_scanned → enrolled students with NO record for that date

    This lets the review page show the full class list so the teacher
    can mark non-scanners as leave/event rather than just absent.

    Returns:
      [
        {
          'date'       : date,
          'scanned'    : [
              {'record': Attendance, 'student': Student},
              ...
          ],
          'not_scanned': [
              {'student': Student},
              ...
          ],
          'scanned_count'    : int,
          'not_scanned_count': int,
          'total'            : int,
        },
        ...
      ]
    Ordered newest date first.
    """
    from collections import defaultdict

    teacher = _get_teacher(teacher_user)
    if not teacher:
        return []

    subject = Subject.query.get(subject_id)
    if not subject:
        return []

    # Security: teacher must own this subject
    if not teacher_user.is_hod:
        assigned_ids = [s.id for s in teacher.subjects.all()]
        if subject.id not in assigned_ids:
            return []

    # All pending (QR-scanned) records for this subject
    pending_records = (
        Attendance.query
        .filter_by(
            subject_id = subject.id,
            status     = 'pending',
            is_qr_scan = True,
        )
        .order_by(Attendance.date.desc(), Attendance.student_id)
        .all()
    )

    if not pending_records:
        return []

    # Group pending records by date
    by_date = defaultdict(list)
    for rec in pending_records:
        by_date[rec.date].append(rec)

    # All enrolled students for this subject
    enrolled = _get_enrolled_students(subject)
    enrolled_by_id = {s.id: s for s in enrolled}

    result = []
    for att_date in sorted(by_date.keys(), reverse=True):
        pending_recs = by_date[att_date]

        # Student IDs who scanned on this date
        scanned_student_ids = {rec.student_id for rec in pending_recs}

        # Build scanned list
        scanned = [
            {'record': rec, 'student': rec.student}
            for rec in pending_recs
        ]

        # Build not-scanned list — enrolled students with no record
        # on this date (neither pending nor any other status)
        existing_ids_on_date = {
            r.student_id
            for r in Attendance.query.filter_by(
                subject_id = subject.id,
                date       = att_date,
            ).all()
        }

        not_scanned = [
            {'student': student}
            for student in enrolled
            if student.id not in existing_ids_on_date
        ]

        result.append({
            'date'             : att_date,
            'scanned'          : scanned,
            'not_scanned'      : not_scanned,
            'scanned_count'    : len(scanned),
            'not_scanned_count': len(not_scanned),
            'total'            : len(scanned) + len(not_scanned),
        })

    return result


def review_qr_submissions(teacher_user, subject_id, review_date,
                          scanned_map, not_scanned_map):
    """
    Teacher confirms the full class list for a QR session date.

    Called by: POST /teacher/review-qr/<subject_id>

    TWO input maps (both from the form):
    ─────────────────────────────────────
    scanned_map: {attendance_id (int): new_status (str)}
      Students who scanned the QR — their pending record gets confirmed.
      Allowed statuses: REVIEW_STATUSES (present, leave, event, no_class)

    not_scanned_map: {student_id (int): new_status (str)}
      Students who did NOT scan — a fresh record is created for each.
      Allowed statuses: REVIEW_STATUSES + 'absent'
      Teacher explicitly chooses for each — no auto-absent assumption.

    Returns: (True, summary_dict) on success
             (False, error_str)   on failure
    """
    ALL_REVIEW = REVIEW_STATUSES + ('absent',)

    teacher = _get_teacher(teacher_user)
    if not teacher:
        return False, 'Teacher profile not found.'

    subject = Subject.query.get(subject_id)
    if not subject:
        return False, 'Subject not found.'

    if not teacher_user.is_hod:
        assigned_ids = [s.id for s in teacher.subjects.all()]
        if subject.id not in assigned_ids:
            return False, 'You are not assigned to this subject.'

    if not scanned_map and not not_scanned_map:
        return False, 'No review data submitted.'

    # Validate all statuses before writing anything
    for att_id, status in scanned_map.items():
        if status not in REVIEW_STATUSES:
            return False, (
                f'Invalid status "{status}" for attendance #{att_id}. '
                f'Allowed: {", ".join(REVIEW_STATUSES)}.'
            )
    for stu_id, status in not_scanned_map.items():
        if status not in ALL_REVIEW:
            return False, (
                f'Invalid status "{status}" for student #{stu_id}. '
                f'Allowed: {", ".join(ALL_REVIEW)}.'
            )

    # Step 1: Confirm pending (scanned) records
    reviewed = 0
    for att_id, new_status in scanned_map.items():
        record = Attendance.query.get(att_id)
        if not record:
            continue
        if record.subject_id != subject.id:
            continue
        if record.status != 'pending':
            continue
        record.apply_teacher_review(new_status, teacher)
        reviewed += 1

    # Step 2: Create records for non-scanned students
    existing_ids = {
        r.student_id
        for r in Attendance.query.filter_by(
            subject_id = subject.id,
            date       = review_date,
        ).all()
    }

    explicitly_marked = 0
    for stu_id, new_status in not_scanned_map.items():
        if stu_id in existing_ids:
            continue
        student = Student.query.get(stu_id)
        if not student:
            continue
        db.session.add(Attendance(
            student_id   = student.id,
            subject_id   = subject.id,
            marked_by_id = teacher.id,
            date         = review_date,
            status       = new_status,
            semester     = student.semester,
            is_qr_scan   = False,
        ))
        explicitly_marked += 1

    db.session.commit()

    # Fire low-attendance notifications
    from app.services.student_service import check_and_notify_low_attendance
    for student in _get_enrolled_students(subject):
        check_and_notify_low_attendance(student.id)

    message = (
        f'Review complete for {review_date.strftime("%d %b %Y")}: '
        f'{reviewed} QR scan(s) confirmed, '
        f'{explicitly_marked} non-scanner(s) marked by teacher.'
    )

    return True, {
        'reviewed'         : reviewed,
        'explicitly_marked': explicitly_marked,
        'message'          : message,
    }


def get_subject_attendance_history(teacher_user, subject_id, limit=30):
    """
    Return recent attendance sessions for a subject, grouped by date.
    """
    teacher = _get_teacher(teacher_user)
    if not teacher:
        return []

    subject = Subject.query.get(subject_id)
    if not subject:
        return []

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
        no_class = sum(1 for r in records if r.status == 'no_class')
        pending  = sum(1 for r in records if r.status == 'pending')
        conducted = present + absent   # only present+absent count

        history.append({
            'date'    : att_date,
            'records' : records,
            'present' : present,
            'absent'  : absent,
            'leave'   : on_leave,
            'event'   : on_event,
            'no_class': no_class,
            'pending' : pending,
            'total'   : len(records),
            'pct'     : round(present / conducted * 100, 1)
                        if conducted > 0 else 0.0,
        })

    return history


def get_student_subject_attendance(subject_id, student_id):
    """
    All attendance records for ONE student in ONE subject.
    """
    return (
        Attendance.query
        .filter_by(subject_id=subject_id, student_id=student_id)
        .order_by(Attendance.date.desc())
        .all()
    )