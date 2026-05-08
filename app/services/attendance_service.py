# from datetime import date, datetime, timedelta
# from collections import defaultdict
# from app import db
# from app.models.attendance import Attendance
# from app.models.student    import Student
# from app.models.subject    import Subject
# from app.models.teacher    import Teacher
# from app.models.user       import User

# # ══════════════════════════════════════════════════════════════════════
# #  THRESHOLDS
# # ══════════════════════════════════════════════════════════════════════
# THRESHOLD_LOW       = 75.0
# THRESHOLD_WARNING   = 85.0
# MIN_EDIT_REASON_LEN = 5

# # Statuses the HOD is allowed to set via the edit form.
# # Excludes 'pending' — HOD should not be setting records to pending.
# # The teacher handles pending→final via the QR review flow.
# HOD_EDITABLE_STATUSES = ('present', 'absent', 'leave', 'event', 'no_class')


# # ══════════════════════════════════════════════════════════════════════
# #  CORE CALCULATION FUNCTIONS
# # ══════════════════════════════════════════════════════════════════════

# def calculate_percentage(records):
#     """
#     The single, canonical attendance % calculation.
#     Accepts a list of Attendance objects.

#     STATUS COUNTING:
#       present   → counted in both present_days AND conducted_days
#       absent    → counted in conducted_days only (hurts %)
#       leave     → excluded from both (neutral)
#       event     → excluded from both (neutral)
#       no_class  → excluded from both (neutral — class didn't happen)
#       pending   → excluded from both (neutral — awaiting review)

#     Returns a dict:
#       present   → int count of 'present' records
#       absent    → int count of 'absent' records
#       leave     → int count of 'leave' records
#       event     → int count of 'event' records
#       no_class  → int count of 'no_class' records
#       pending   → int count of 'pending' records
#       conducted → present + absent  (denominator — others excluded)
#       total     → all records including neutral ones
#       pct       → float percentage (0.0 if no conducted classes)
#       status    → 'ok' | 'warning' | 'low' | 'no_data'
#     """
#     present  = sum(1 for r in records if r.status == 'present')
#     absent   = sum(1 for r in records if r.status == 'absent')
#     leave    = sum(1 for r in records if r.status == 'leave')
#     event    = sum(1 for r in records if r.status == 'event')
#     no_class = sum(1 for r in records if r.status == 'no_class')
#     pending  = sum(1 for r in records if r.status == 'pending')
#     total    = len(records)

#     # Only present + absent count as "conducted"
#     # All neutral statuses (leave, event, no_class, pending) are excluded
#     conducted = present + absent

#     if conducted == 0:
#         pct        = 0.0
#         att_status = 'no_data'
#     else:
#         pct        = round((present / conducted) * 100, 2)
#         att_status = (
#             'low'     if pct < THRESHOLD_LOW     else
#             'warning' if pct < THRESHOLD_WARNING else
#             'ok'
#         )

#     return {
#         'present'  : present,
#         'absent'   : absent,
#         'leave'    : leave,
#         'event'    : event,
#         'no_class' : no_class,
#         'pending'  : pending,
#         'conducted': conducted,
#         'total'    : total,
#         'pct'      : pct,
#         'status'   : att_status,
#     }


# def calculate_required_classes(current_pct, conducted, target_pct=75.0):
#     """
#     How many consecutive present classes does a student need
#     to reach the target attendance %?

#     Formula derivation:
#       new_pct = (present + x) / (conducted + x) × 100 ≥ target
#       x ≥ (target/100 × conducted - present) / (1 - target/100)

#     Returns:
#       0  → already at or above target
#       +n → classes needed to reach target
#       -1 → mathematically unreachable (target = 100% with absents)
#     """
#     if conducted == 0:
#         return 0
#     present = round(current_pct / 100 * conducted)

#     if current_pct >= target_pct:
#         return 0

#     target_fraction = target_pct / 100
#     denominator     = 1 - target_fraction

#     if denominator <= 0:
#         return -1

#     needed = (target_fraction * conducted - present) / denominator
#     return max(0, int(needed) + 1)


# def calculate_can_miss(current_pct, conducted, target_pct=75.0):
#     """
#     How many more classes can this student miss and still stay
#     above the target %?

#     Formula:
#       x ≤ present / (target/100) - conducted

#     Returns non-negative int (0 means cannot miss any more).
#     """
#     if conducted == 0:
#         return 0
#     present = round(current_pct / 100 * conducted)
#     target_fraction = target_pct / 100

#     if target_fraction == 0:
#         return 999

#     can_miss = present / target_fraction - conducted
#     return max(0, int(can_miss))


# # ══════════════════════════════════════════════════════════════════════
# #  STUDENT-LEVEL REPORTS
# # ══════════════════════════════════════════════════════════════════════

# def get_student_attendance_summary(student_id, semester=None):
#     """
#     Full attendance summary for ONE student.
#     Returns overall % and per-subject breakdown.

#     semester: filters to a specific semester (defaults to current).

#     Returns a dict:
#       overall   → calculate_percentage() result across all subjects
#       subjects  → list of per-subject dicts (sorted by subject name)
#       student   → Student object
#       semester  → which semester was computed
#     """
#     student = Student.query.get(student_id)
#     if not student:
#         return None

#     target_sem  = semester or student.semester
#     all_records = student.attendance_records.filter_by(
#         semester=target_sem
#     ).all()

#     overall = calculate_percentage(all_records)

#     subject_map = defaultdict(list)
#     for r in all_records:
#         subject_map[r.subject_id].append(r)

#     subjects_data = []
#     for subj_id, records in subject_map.items():
#         subj = Subject.query.get(subj_id)
#         if not subj:
#             continue
#         result = calculate_percentage(records)
#         result['subject']        = subj
#         result['classes_needed'] = calculate_required_classes(
#             result['pct'], result['conducted']
#         )
#         result['can_miss'] = calculate_can_miss(
#             result['pct'], result['conducted']
#         )
#         subjects_data.append(result)

#     subjects_data.sort(key=lambda x: x['subject'].name)

#     return {
#         'student'      : student,
#         'semester'     : target_sem,
#         'overall'      : overall,
#         'subjects'     : subjects_data,
#         'is_at_risk'   : overall['pct'] < THRESHOLD_LOW and overall['conducted'] > 0,
#         'total_classes_needed': calculate_required_classes(
#             overall['pct'], overall['conducted']
#         ),
#     }


# def get_department_attendance_report(dept_id, semester=None, program_type=None):
#     """
#     Attendance overview for every active student in a department.
#     Used by HOD for department-level report.
#     Returns list sorted by attendance % ascending (lowest first).
#     """
#     q = (
#         Student.query
#         .filter_by(department_id=dept_id, is_graduated=False)
#         .join(Student.user)
#         .filter(User.is_active == True)
#     )
#     if semester:
#         q = q.filter(Student.semester == semester)
#     if program_type:
#         q = q.filter(Student.program_type == program_type)

#     students = q.all()
#     rows = []

#     for student in students:
#         target_sem = semester or student.semester
#         records    = student.attendance_records.filter_by(semester=target_sem).all()
#         result     = calculate_percentage(records)
#         rows.append({
#             'student'   : student,
#             'semester'  : target_sem,
#             'pct'       : result['pct'],
#             'present'   : result['present'],
#             'absent'    : result['absent'],
#             'leave'     : result['leave'],
#             'event'     : result['event'],
#             'no_class'  : result['no_class'],
#             'pending'   : result['pending'],
#             'conducted' : result['conducted'],
#             'att_status': result['status'],
#         })

#     rows.sort(key=lambda r: r['pct'])
#     return rows


# # ══════════════════════════════════════════════════════════════════════
# #  HOD ATTENDANCE EDITING
# # ══════════════════════════════════════════════════════════════════════

# def search_attendance_records(hod_user, filters=None):
#     """
#     Search attendance records in the HOD's department.

#     filters dict keys (all optional):
#       subject_id  → int
#       student_id  → int
#       date_from   → date
#       date_to     → date
#       status      → str
#       edited_only → bool
#       semester    → int

#     Returns list of Attendance records (max 200).
#     """
#     hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
#     if not hod:
#         return []

#     filters = filters or {}

#     q = (
#         Attendance.query
#         .join(Attendance.student)
#         .filter(Student.department_id == hod.department_id)
#         .order_by(Attendance.date.desc(), Attendance.student_id)
#     )

#     if filters.get('subject_id'):
#         q = q.filter(Attendance.subject_id == filters['subject_id'])
#     if filters.get('student_id'):
#         q = q.filter(Attendance.student_id == filters['student_id'])
#     if filters.get('date_from'):
#         q = q.filter(Attendance.date >= filters['date_from'])
#     if filters.get('date_to'):
#         q = q.filter(Attendance.date <= filters['date_to'])
#     if filters.get('status'):
#         q = q.filter(Attendance.status == filters['status'])
#     if filters.get('edited_only'):
#         q = q.filter(Attendance.is_edited == True)
#     if filters.get('semester'):
#         q = q.filter(Attendance.semester == filters['semester'])

#     return q.limit(200).all()


# def hod_edit_attendance(hod_user, attendance_id, new_status, reason):
#     """
#     HOD edits an existing attendance record.

#     RULES:
#       1. HOD must own the student's department
#       2. new_status must be in HOD_EDITABLE_STATUSES
#          (excludes 'pending' — that's handled by teacher QR review)
#       3. reason must be at least MIN_EDIT_REASON_LEN characters
#       4. Original value preserved in original_status

#     Returns: (record, None) on success
#              (None,   error) on failure
#     """
#     hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
#     if not hod:
#         return None, 'HOD profile not found.'

#     record = Attendance.query.get(attendance_id)
#     if not record:
#         return None, 'Attendance record not found.'

#     if record.student.department_id != hod.department_id:
#         return None, 'This record belongs to a different department.'

#     # HOD cannot set status to 'pending' — that is QR-only
#     if new_status not in HOD_EDITABLE_STATUSES:
#         return None, (
#             f'Invalid status "{new_status}". '
#             f'Allowed: {", ".join(HOD_EDITABLE_STATUSES)}.'
#         )

#     reason = reason.strip() if reason else ''
#     if len(reason) < MIN_EDIT_REASON_LEN:
#         return None, (
#             f'A reason of at least {MIN_EDIT_REASON_LEN} characters '
#             f'is required for editing attendance records.'
#         )

#     if record.status == new_status:
#         return None, (
#             f'Status is already "{new_status}". No change made.'
#         )

#     record.apply_hod_edit(new_status, reason, hod)
#     db.session.commit()
#     return record, None


# def get_edit_audit_log(hod_user, limit=50):
#     """
#     Most recent HOD edits for this department — newest first.
#     """
#     hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
#     if not hod:
#         return []

#     return (
#         Attendance.query
#         .join(Attendance.student)
#         .filter(
#             Student.department_id == hod.department_id,
#             Attendance.is_edited  == True
#         )
#         .order_by(Attendance.edited_at.desc())
#         .limit(limit)
#         .all()
#     )


# # ══════════════════════════════════════════════════════════════════════
# #  DAILY SUMMARY
# # ══════════════════════════════════════════════════════════════════════

# def get_daily_summary(dept_id, target_date=None):
#     """
#     For a given date, show present/absent/leave counts across
#     all subjects in the department. Used by principal/HOD widgets.
#     """
#     target_date = target_date or date.today()

#     records = (
#         Attendance.query
#         .join(Attendance.student)
#         .filter(
#             Student.department_id == dept_id,
#             Attendance.date       == target_date
#         )
#         .all()
#     )

#     result = calculate_percentage(records)
#     result['date']    = target_date
#     result['dept_id'] = dept_id
#     return result


#############0------------fix minor bugs
"""
ATTENDANCE SERVICE
==================
The dedicated attendance calculation and reporting engine.

All percentage calculations live here — single source of truth.
Any route, template, or test that needs an attendance number
calls this service rather than computing it inline.

FORMULA (decided and documented here):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  attendance % = (present_days / conducted_days) × 100

  WHERE:
    present_days   = records with status = 'present'
    conducted_days = records with status IN ('present', 'absent')

  NEUTRAL STATUSES — excluded from BOTH sides of the formula:
    leave     → authorised absence (medical, personal)
    event     → official college duty (sports, fest, seminar)
    no_class  → class cancelled / holiday / Sunday
    pending   → QR scanned, awaiting teacher review

  WHY pending is neutral:
    The student submitted via QR — we know they were there.
    But the teacher has not confirmed yet.
    Treating it as 'absent' temporarily would unfairly hurt %.
    Treating it as 'present' before review would inflate %.
    Neutral means: record exists, prevents double-scan, zero % impact.

  EXAMPLE:
    20 classes total:
      12 present, 4 absent, 2 leave, 1 event, 1 no_class

    conducted_days = 12 + 4          = 16   (others excluded)
    present_days   = 12
    attendance %   = 12/16 × 100     = 75.0%

LOW ATTENDANCE THRESHOLDS:
  < 75% → LOW     (student risks debarment)
  < 85% → WARNING (student should improve)
  ≥ 85% → OK
"""

from datetime import date, datetime, timedelta
from collections import defaultdict
from app import db
from app.models.attendance import Attendance
from app.models.student    import Student
from app.models.subject    import Subject
from app.models.teacher    import Teacher
from app.models.user       import User

# ══════════════════════════════════════════════════════════════════════
#  THRESHOLDS
# ══════════════════════════════════════════════════════════════════════
THRESHOLD_LOW       = 75.0
THRESHOLD_WARNING   = 85.0
MIN_EDIT_REASON_LEN = 5

# Statuses the HOD is allowed to set via the edit form.
# Excludes 'pending' — HOD should not be setting records to pending.
# The teacher handles pending→final via the QR review flow.
HOD_EDITABLE_STATUSES = ('present', 'absent', 'leave', 'event', 'no_class')


# ══════════════════════════════════════════════════════════════════════
#  CORE CALCULATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def calculate_percentage(records):
    """
    The single, canonical attendance % calculation.
    Accepts a list of Attendance objects.

    STATUS COUNTING:
      present   → counted in both present_days AND conducted_days
      absent    → counted in conducted_days only (hurts %)
      leave     → excluded from both (neutral)
      event     → excluded from both (neutral)
      no_class  → excluded from both (neutral — class didn't happen)
      pending   → excluded from both (neutral — awaiting review)

    Returns a dict:
      present   → int count of 'present' records
      absent    → int count of 'absent' records
      leave     → int count of 'leave' records
      event     → int count of 'event' records
      no_class  → int count of 'no_class' records
      pending   → int count of 'pending' records
      conducted → present + absent  (denominator — others excluded)
      total     → all records including neutral ones
      pct       → float percentage (0.0 if no conducted classes)
      status    → 'ok' | 'warning' | 'low' | 'no_data'
    """
    present  = sum(1 for r in records if r.status == 'present')
    absent   = sum(1 for r in records if r.status == 'absent')
    leave    = sum(1 for r in records if r.status == 'leave')
    event    = sum(1 for r in records if r.status == 'event')
    no_class = sum(1 for r in records if r.status == 'no_class')
    pending  = sum(1 for r in records if r.status == 'pending')
    total    = len(records)

    # Only present + absent count as "conducted"
    # All neutral statuses (leave, event, no_class, pending) are excluded
    conducted = present + absent

    if conducted == 0:
        pct        = 0.0
        att_status = 'no_data'
    else:
        pct        = round((present / conducted) * 100, 2)
        att_status = (
            'low'     if pct < THRESHOLD_LOW     else
            'warning' if pct < THRESHOLD_WARNING else
            'ok'
        )

    return {
        'present'  : present,
        'absent'   : absent,
        'leave'    : leave,
        'event'    : event,
        'no_class' : no_class,
        'pending'  : pending,
        'conducted': conducted,
        'total'    : total,
        'pct'      : pct,
        'status'   : att_status,
    }


def calculate_required_classes(current_pct, conducted, target_pct=75.0):
    """
    How many consecutive present classes does a student need
    to reach the target attendance %?

    Formula derivation:
      new_pct = (present + x) / (conducted + x) × 100 ≥ target
      x ≥ (target/100 × conducted - present) / (1 - target/100)

    Returns:
      0  → already at or above target
      +n → classes needed to reach target
      -1 → mathematically unreachable (target = 100% with absents)
    """
    if conducted == 0:
        return 0
    present = round(current_pct / 100 * conducted)

    if current_pct >= target_pct:
        return 0

    target_fraction = target_pct / 100
    denominator     = 1 - target_fraction

    if denominator <= 0:
        return -1

    needed = (target_fraction * conducted - present) / denominator
    return max(0, int(needed) + 1)


def calculate_can_miss(current_pct, conducted, target_pct=75.0):
    """
    How many more classes can this student miss and still stay
    above the target %?

    Formula:
      x ≤ present / (target/100) - conducted

    Returns non-negative int (0 means cannot miss any more).
    """
    if conducted == 0:
        return 0
    present = round(current_pct / 100 * conducted)
    target_fraction = target_pct / 100

    if target_fraction == 0:
        return 999

    can_miss = present / target_fraction - conducted
    return max(0, int(can_miss))


# ══════════════════════════════════════════════════════════════════════
#  STUDENT-LEVEL REPORTS
# ══════════════════════════════════════════════════════════════════════

def get_student_attendance_summary(student_id, semester=None):
    """
    Full attendance summary for ONE student.
    Returns overall % and per-subject breakdown.

    semester: filters to a specific semester (defaults to current).

    Returns a dict:
      overall   → calculate_percentage() result across all subjects
      subjects  → list of per-subject dicts (sorted by subject name)
      student   → Student object
      semester  → which semester was computed
    """
    student = Student.query.get(student_id)
    if not student:
        return None

    target_sem  = semester or student.semester
    all_records = student.attendance_records.filter_by(
        semester=target_sem
    ).all()

    overall = calculate_percentage(all_records)

    subject_map = defaultdict(list)
    for r in all_records:
        subject_map[r.subject_id].append(r)

    subjects_data = []
    for subj_id, records in subject_map.items():
        subj = Subject.query.get(subj_id)
        if not subj:
            continue
        result = calculate_percentage(records)
        result['subject']        = subj
        result['classes_needed'] = calculate_required_classes(
            result['pct'], result['conducted']
        )
        result['can_miss'] = calculate_can_miss(
            result['pct'], result['conducted']
        )
        subjects_data.append(result)

    subjects_data.sort(key=lambda x: x['subject'].name)

    return {
        'student'      : student,
        'semester'     : target_sem,
        'overall'      : overall,
        'subjects'     : subjects_data,
        'is_at_risk'   : overall['pct'] < THRESHOLD_LOW and overall['conducted'] > 0,
        'total_classes_needed': calculate_required_classes(
            overall['pct'], overall['conducted']
        ),
    }


def get_department_attendance_report(dept_id, semester=None, program_type=None):
    """
    Attendance overview for every active student in a department.
    Used by HOD for department-level report.
    Returns list sorted by attendance % ascending (lowest first).
    """
    q = (
        Student.query
        .filter_by(department_id=dept_id, is_graduated=False)
        .join(Student.user)
        .filter(User.is_active == True)
    )
    if semester:
        q = q.filter(Student.semester == semester)
    if program_type:
        q = q.filter(Student.program_type == program_type)

    students = q.all()
    rows = []

    for student in students:
        target_sem = semester or student.semester
        records    = student.attendance_records.filter_by(semester=target_sem).all()
        result     = calculate_percentage(records)
        rows.append({
            'student'   : student,
            'semester'  : target_sem,
            'pct'       : result['pct'],
            'present'   : result['present'],
            'absent'    : result['absent'],
            'leave'     : result['leave'],
            'event'     : result['event'],
            'no_class'  : result['no_class'],
            'pending'   : result['pending'],
            'conducted' : result['conducted'],
            'att_status': result['status'],
        })

    rows.sort(key=lambda r: r['pct'])
    return rows


# ══════════════════════════════════════════════════════════════════════
#  HOD ATTENDANCE EDITING
# ══════════════════════════════════════════════════════════════════════

def search_attendance_records(hod_user, filters=None):
    """
    Search attendance records in the HOD's department.

    filters dict keys (all optional):
      subject_id  → int
      student_id  → int
      date_from   → date
      date_to     → date
      status      → str
      edited_only → bool
      semester    → int

    Returns list of Attendance records (max 200).
    """
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return []

    filters = filters or {}

    q = (
        Attendance.query
        .join(Attendance.student)
        .filter(Student.department_id == hod.department_id)
        .order_by(Attendance.date.desc(), Attendance.student_id)
    )

    if filters.get('subject_id'):
        q = q.filter(Attendance.subject_id == filters['subject_id'])
    if filters.get('student_id'):
        q = q.filter(Attendance.student_id == filters['student_id'])
    if filters.get('date_from'):
        q = q.filter(Attendance.date >= filters['date_from'])
    if filters.get('date_to'):
        q = q.filter(Attendance.date <= filters['date_to'])
    if filters.get('status'):
        q = q.filter(Attendance.status == filters['status'])
    if filters.get('edited_only'):
        q = q.filter(Attendance.is_edited == True)
    if filters.get('semester'):
        q = q.filter(Attendance.semester == filters['semester'])

    return q.limit(200).all()


def hod_edit_attendance(hod_user, attendance_id, new_status, reason):
    """
    HOD edits an existing attendance record.

    RULES:
      1. HOD must own the student's department
      2. new_status must be in HOD_EDITABLE_STATUSES
         (excludes 'pending' — that's handled by teacher QR review)
      3. reason must be at least MIN_EDIT_REASON_LEN characters
      4. Original value preserved in original_status

    Returns: (record, None) on success
             (None,   error) on failure
    """
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return None, 'HOD profile not found.'

    record = Attendance.query.get(attendance_id)
    if not record:
        return None, 'Attendance record not found.'

    if record.student.department_id != hod.department_id:
        return None, 'This record belongs to a different department.'

    # HOD cannot set status to 'pending' — that is QR-only
    if new_status not in HOD_EDITABLE_STATUSES:
        return None, (
            f'Invalid status "{new_status}". '
            f'Allowed: {", ".join(HOD_EDITABLE_STATUSES)}.'
        )

    reason = reason.strip() if reason else ''
    if len(reason) < MIN_EDIT_REASON_LEN:
        return None, (
            f'A reason of at least {MIN_EDIT_REASON_LEN} characters '
            f'is required for editing attendance records.'
        )

    if record.status == new_status:
        return None, (
            f'Status is already "{new_status}". No change made.'
        )

    record.apply_hod_edit(new_status, reason, hod)
    db.session.commit()
    return record, None


def get_edit_audit_log(hod_user, limit=50):
    """
    Most recent HOD edits for this department — newest first.
    """
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return []

    return (
        Attendance.query
        .join(Attendance.student)
        .filter(
            Student.department_id == hod.department_id,
            Attendance.is_edited  == True
        )
        .order_by(Attendance.edited_at.desc())
        .limit(limit)
        .all()
    )


# ══════════════════════════════════════════════════════════════════════
#  DAILY SUMMARY
# ══════════════════════════════════════════════════════════════════════

def get_daily_summary(dept_id, target_date=None):
    """
    For a given date, show present/absent/leave counts across
    all subjects in the department. Used by principal/HOD widgets.
    """
    target_date = target_date or date.today()

    records = (
        Attendance.query
        .join(Attendance.student)
        .filter(
            Student.department_id == dept_id,
            Attendance.date       == target_date
        )
        .all()
    )

    result = calculate_percentage(records)
    result['date']    = target_date
    result['dept_id'] = dept_id
    return result