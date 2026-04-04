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
                     i.e. rows where status NOT IN ('leave', 'event')

  WHY leave/event are EXCLUDED from denominator:
    leave  → student had authorised absence (medical, personal)
             They did not skip class; they had permission.
             Penalising them in % would be unfair.
    event  → student was on official college duty (sports, fest, seminar)
             The college sent them; counting it as absence is wrong.
    Both are NEUTRAL — excluded from both numerator AND denominator.

  EXAMPLE:
    20 classes total:
      12 present, 4 absent, 3 leave, 1 event

    conducted_days = 12 + 4          = 16   (leave + event excluded)
    present_days   = 12
    attendance %   = 12/16 × 100     = 75.0%

    If we had used all 20: 12/20 = 60% — unfair to the student.

LOW ATTENDANCE THRESHOLD:
  < 75% → flagged as LOW (student risks debarment)
  < 85% → flagged as WARNING (student should improve)
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
THRESHOLD_LOW      = 75.0   # below this → risk of debarment
THRESHOLD_WARNING  = 85.0   # below this → should improve
MIN_EDIT_REASON_LEN = 5     # HOD edit reason must be at least this long


# ══════════════════════════════════════════════════════════════════════
#  CORE CALCULATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def calculate_percentage(records):
    """
    The single, canonical attendance % calculation.
    Accepts a list of Attendance objects.

    Returns a dict:
      present   → count of 'present' records
      absent    → count of 'absent' records
      leave     → count of 'leave' records
      event     → count of 'event' records
      conducted → present + absent  (denominator)
      total     → all records
      pct       → float percentage (0.0 if no conducted classes)
      status    → 'ok' | 'warning' | 'low' | 'no_data'
    """
    present   = sum(1 for r in records if r.status == 'present')
    absent    = sum(1 for r in records if r.status == 'absent')
    leave     = sum(1 for r in records if r.status == 'leave')
    event     = sum(1 for r in records if r.status == 'event')
    total     = len(records)
    conducted = present + absent          # leave + event excluded

    if conducted == 0:
        pct = 0.0
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
        'conducted': conducted,
        'total'    : total,
        'pct'      : pct,
        'status'   : att_status,
    }


def calculate_required_classes(current_pct, conducted, target_pct=75.0):
    """
    Answer: "how many consecutive present classes does a student need
    to reach the target attendance %?"

    Formula derivation:
      new_pct = (present + x) / (conducted + x) × 100 ≥ target
      present + x ≥ target/100 × (conducted + x)
      present + x ≥ target/100 × conducted + target/100 × x
      x(1 - target/100) ≥ target/100 × conducted - present
      x ≥ (target/100 × conducted - present) / (1 - target/100)

    Returns:
      0 if already at or above target
      positive int — classes needed to reach target
      -1 if target is already unreachable (would need infinite classes)
    """
    if conducted == 0:
        return 0
    present = round(current_pct / 100 * conducted)

    if current_pct >= target_pct:
        return 0

    target_fraction = target_pct / 100
    denominator     = 1 - target_fraction

    if denominator <= 0:
        return -1    # target_pct = 100% — mathematically unreachable unless absent=0

    needed = (target_fraction * conducted - present) / denominator
    return max(0, int(needed) + 1)     # round up


def calculate_can_miss(current_pct, conducted, target_pct=75.0):
    """
    Answer: "how many classes can this student miss and still stay
    above the target %?"

    Formula derivation:
      new_pct = present / (conducted + x) × 100 ≥ target
      present ≥ target/100 × (conducted + x)
      present / (target/100) ≥ conducted + x
      x ≤ present / (target/100) - conducted

    Returns:
      non-negative int — classes the student can safely miss
      0 if they cannot miss any
    """
    if conducted == 0:
        return 0
    present = round(current_pct / 100 * conducted)
    target_fraction = target_pct / 100

    if target_fraction == 0:
        return 999    # no minimum required — can miss everything

    can_miss = present / target_fraction - conducted
    return max(0, int(can_miss))


# ══════════════════════════════════════════════════════════════════════
#  STUDENT-LEVEL REPORTS
# ══════════════════════════════════════════════════════════════════════

def get_student_attendance_summary(student_id, semester=None):
    """
    Full attendance summary for ONE student.
    Returns overall % and per-subject breakdown.

    semester: if provided, filters to that specific semester.
              defaults to student's CURRENT semester.

    Returns a dict:
      overall   → calculate_percentage() result for all subjects combined
      subjects  → list of per-subject dicts (sorted by subject name)
      student   → the Student object
      semester  → which semester was computed
    """
    student = Student.query.get(student_id)
    if not student:
        return None

    target_sem = semester or student.semester

    # All records for this semester
    all_records = student.attendance_records.filter_by(
        semester=target_sem
    ).all()

    overall = calculate_percentage(all_records)

    # Per-subject breakdown
    subject_map = defaultdict(list)
    for r in all_records:
        subject_map[r.subject_id].append(r)

    subjects_data = []
    for subj_id, records in subject_map.items():
        subj   = Subject.query.get(subj_id)
        if not subj:
            continue
        result = calculate_percentage(records)
        result['subject']          = subj
        result['classes_needed']   = calculate_required_classes(
            result['pct'], result['conducted']
        )
        result['can_miss']         = calculate_can_miss(
            result['pct'], result['conducted']
        )
        subjects_data.append(result)

    subjects_data.sort(key=lambda x: x['subject'].name)

    return {
        'student'     : student,
        'semester'    : target_sem,
        'overall'     : overall,
        'subjects'    : subjects_data,
        'is_at_risk'  : overall['pct'] < THRESHOLD_LOW and overall['conducted'] > 0,
        'total_classes_needed': calculate_required_classes(
            overall['pct'], overall['conducted']
        ),
    }


def get_department_attendance_report(dept_id, semester=None, program_type=None):
    """
    Attendance overview for every student in a department.
    Used by HOD for the department-level report.

    Returns a list of student summaries, sorted by attendance % ascending
    (lowest first — most at-risk students shown at top).
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
        records = student.attendance_records.filter_by(semester=target_sem).all()
        result  = calculate_percentage(records)
        rows.append({
            'student'  : student,
            'semester' : target_sem,
            'pct'      : result['pct'],
            'present'  : result['present'],
            'absent'   : result['absent'],
            'leave'    : result['leave'],
            'event'    : result['event'],
            'conducted': result['conducted'],
            'att_status': result['status'],
        })

    # Sort: most at-risk (lowest %) first
    rows.sort(key=lambda r: r['pct'])
    return rows


# ══════════════════════════════════════════════════════════════════════
#  HOD ATTENDANCE EDITING
# ══════════════════════════════════════════════════════════════════════

def search_attendance_records(hod_user, filters=None):
    """
    Search attendance records in the HOD's department.
    Supports filtering by: subject, student, date range, status.

    filters dict keys (all optional):
      subject_id    → int
      student_id    → int
      date_from     → date
      date_to       → date
      status        → str  ('present'|'absent'|'leave'|'event')
      edited_only   → bool (only show HOD-edited records)
      semester      → int

    Returns a list of Attendance records.
    """
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return []

    filters = filters or {}

    # Base query: only students in HOD's department
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

    return q.limit(200).all()   # cap at 200 rows per search


def hod_edit_attendance(hod_user, attendance_id, new_status, reason):
    """
    HOD edits an existing attendance record.

    RULES enforced here:
      1. HOD must own the student's department
      2. new_status must be one of the four valid values
      3. reason must be at least MIN_EDIT_REASON_LEN characters
      4. The ORIGINAL value is preserved in original_status
      5. Who edited, when, and why are all recorded

    Returns: (record, None) on success
             (None, error_msg) on any failure
    """
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return None, 'HOD profile not found.'

    record = Attendance.query.get(attendance_id)
    if not record:
        return None, 'Attendance record not found.'

    # Ownership check: student must be in HOD's department
    if record.student.department_id != hod.department_id:
        return None, 'This record belongs to a different department.'

    # Validate new status
    if new_status not in Attendance.VALID_STATUSES:
        return None, (
            f'Invalid status "{new_status}". '
            f'Allowed: {", ".join(Attendance.VALID_STATUSES)}.'
        )

    # Validate reason
    reason = reason.strip() if reason else ''
    if len(reason) < MIN_EDIT_REASON_LEN:
        return None, (
            f'A reason of at least {MIN_EDIT_REASON_LEN} characters '
            f'is required for editing attendance records.'
        )

    # No-op guard: same status with same reason
    if record.status == new_status:
        return None, (
            f'Status is already "{new_status}". No change made. '
            f'If you want to add a note, change the status first.'
        )

    # Apply the edit — model method handles all field updates
    record.apply_hod_edit(new_status, reason, hod)
    db.session.commit()
    return record, None


def get_edit_audit_log(hod_user, limit=50):
    """
    Return the most recent HOD edits for this department — newest first.
    Used to show an audit trail of all attendance corrections.
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
#  DATE-WISE DAILY SUMMARY
# ══════════════════════════════════════════════════════════════════════

def get_daily_summary(dept_id, target_date=None):
    """
    For a given date, show how many students were present/absent/on leave
    across all subjects in the department.

    Used for a principal/HOD daily overview widget.
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
    result['date']     = target_date
    result['dept_id']  = dept_id
    return result
