"""
GRADUATION SERVICE
==================
This is the single source of truth for ALL graduation logic.

WHY a separate service file?
  Graduation is the most consequential and irreversible action in the
  entire system. It touches the Student model, the User model, and
  creates a permanent audit record. Having it isolated means:
    - Easy to unit-test independently
    - One place to change if rules ever change
    - Route stays thin and unaware of business rules

RULES (hard-coded, system-enforced):
  ┌─────────────┬──────────────────────────────────────────────┐
  │ Program Type│ Valid Graduation Semesters                   │
  ├─────────────┼──────────────────────────────────────────────┤
  │ UG          │ 6 (early/lateral exit) OR 8 (full programme)│
  │ PG          │ 4 (full programme only)                      │
  └─────────────┴──────────────────────────────────────────────┘

  1. Graduation is MANUAL — only HOD triggers it, never automatic.
  2. Graduation is NOT time-based — HOD decides when, regardless of date.
  3. Once graduated: is_graduated=True, User.is_active=False.
  4. Graduated students are FROZEN — no edits, no re-graduation.
  5. All graduation data is stored permanently — never deleted.
  6. Only HOD of the student's own department can graduate them.

EDGE CASES HANDLED:
  ─────────────────
  EC-1: Trying to graduate a student who is already graduated
        → rejected with clear message, graduation_semester shown

  EC-2: Trying to promote a graduated student
        → rejected: "Cannot promote, student has graduated"

  EC-3: Trying to graduate at a non-valid semester (e.g. UG at Sem 4)
        → rejected: "UG students can graduate at Sem 6 or 8 only"

  EC-4: Trying to graduate a student from a different department
        → rejected: "Student does not belong to your department"

  EC-5: Reason is blank or too short
        → rejected: "A graduation reason of at least 10 characters is required"

  EC-6: Bulk-promoting students who are already graduated
        → silently skipped, not counted, listed in skipped_names

  EC-7: HOD has no teacher profile (shouldn't happen, but defensive)
        → rejected: "HOD profile not found"

  EC-8: Trying to graduate a soft-deleted (deactivated, non-graduated) student
        → rejected: "Account is already deactivated"
"""

from datetime import datetime
from app import db
from app.models.student      import Student
from app.models.teacher      import Teacher
from app.models.notification import Notification


# ══════════════════════════════════════════════════════════════════════
#  CONSTANTS
#  Single source of truth for graduation rules.
#  Change these values if the college rules ever change.
# ══════════════════════════════════════════════════════════════════════

GRADUATION_RULES = {
    #  program_type : [list of valid semesters to graduate from]
    'UG': [6, 8],
    'PG': [4],
}

GRADUATION_REASON_MIN_LEN = 10   # characters


# ══════════════════════════════════════════════════════════════════════
#  VALIDATION HELPERS
#  Each returns (True, None) on pass, (False, error_message) on fail.
#  Called by graduate_student() before touching the database.
# ══════════════════════════════════════════════════════════════════════

def _validate_not_already_graduated(student):
    """
    EC-1: Re-graduation prevention.
    Once is_graduated=True, no further action is possible.
    The graduation record is permanent and must not be overwritten.
    """
    if student.is_graduated:
        return False, (
            f'{student.full_name} has already graduated. '
            f'Programme: {student.program_type}, '
            f'Semester: {student.graduation_semester}, '
            f'Year: {student.graduation_year}. '
            f'Graduation records cannot be modified.'
        )
    return True, None


def _validate_account_is_active(student):
    """
    EC-8: Soft-deleted (removed) student guard.
    A student who was removed (user.is_active=False, is_graduated=False)
    is in a deactivated state — they cannot be graduated.
    """
    if not student.user.is_active:
        return False, (
            f'{student.full_name}\'s account is deactivated. '
            f'This student was previously removed. '
            f'Contact the system administrator if this is an error.'
        )
    return True, None


def _validate_graduation_semester(student):
    """
    EC-3: Graduation semester validation.
    The student must be AT a valid graduation semester right now.
    UG → must be at semester 6 or 8.
    PG → must be at semester 4.
    Being at semester 5 (UG) means they have NOT yet reached a
    valid graduation point.
    """
    valid_sems = GRADUATION_RULES.get(student.program_type, [])

    if student.semester not in valid_sems:
        valid_str = ' or '.join(f'Semester {s}' for s in valid_sems)
        return False, (
            f'Cannot graduate {student.full_name} from Semester {student.semester}. '
            f'{student.program_type} students can only graduate at {valid_str}. '
            f'Current semester: {student.semester}.'
        )
    return True, None


def _validate_department_ownership(student, hod_teacher):
    """
    EC-4: Cross-department graduation prevention.
    HOD can only graduate students in THEIR OWN department.
    """
    if student.department_id != hod_teacher.department_id:
        return False, (
            f'Cannot graduate {student.full_name}. '
            f'Student belongs to a different department.'
        )
    return True, None


def _validate_reason(reason):
    """
    EC-5: Reason validation.
    A meaningful reason is mandatory — this is an academic record.
    We enforce a minimum length to prevent trivial entries like "done".
    """
    if not reason or len(reason.strip()) < GRADUATION_REASON_MIN_LEN:
        return False, (
            f'A graduation reason of at least {GRADUATION_REASON_MIN_LEN} '
            f'characters is required. This becomes part of the permanent record.'
        )
    return True, None


# ══════════════════════════════════════════════════════════════════════
#  CORE GRADUATION FUNCTION
# ══════════════════════════════════════════════════════════════════════

def graduate_student(hod_user, student_id, reason):
    """
    Graduate a single student. The most consequential action in the system.

    Runs ALL validations before touching the database.
    If ANY validation fails, returns (None, error_message) and the
    database is NOT modified at all.

    On success:
      - student.is_graduated        = True
      - student.graduation_semester = current semester at time of graduation
      - student.graduation_year     = calendar year of graduation
      - student.graduation_reason   = HOD's reason (permanent record)
      - student.graduated_at        = exact timestamp
      - student.graduated_by_id     = HOD teacher's ID (audit trail)
      - student.user.is_active      = False (login disabled immediately)
      - Notification sent to student

    Returns: (student, None) on success
             (None, error_message) on any validation failure
    """
    # ── Step 1: Get HOD's teacher profile ──────────────────────────
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return None, 'HOD profile not found. Cannot perform graduation.'

    # ── Step 2: Get the student ─────────────────────────────────────
    student = Student.query.get(student_id)
    if not student:
        return None, 'Student not found.'

    # ── Step 3: Run ALL validations (order matters — clearest errors first) ──
    checks = [
        _validate_not_already_graduated(student),  # EC-1
        _validate_account_is_active(student),       # EC-8
        _validate_department_ownership(student, hod),# EC-4
        _validate_graduation_semester(student),     # EC-3
        _validate_reason(reason),                   # EC-5
    ]

    for passed, error_msg in checks:
        if not passed:
            return None, error_msg

    # ── Step 4: All checks passed — perform graduation ──────────────
    now = datetime.utcnow()

    student.is_graduated        = True
    student.graduation_semester = student.semester      # snapshot the semester
    student.graduation_year     = str(now.year)         # calendar year
    student.graduation_reason   = reason.strip()        # HOD's note
    student.graduated_at        = now                   # exact timestamp
    student.graduated_by_id     = hod.id                # who did it

    # Disable login — graduated student cannot log in anymore
    # Their data is fully preserved; only the login is blocked.
    student.user.is_active = False

    # ── Step 5: Notify the student ──────────────────────────────────
    # Even though login is disabled, the notification is stored in DB
    # for administrative records and future audit.
    db.session.add(Notification(
        user_id = student.user_id,
        type    = 'success',
        title   = f'Congratulations — {student.program_type} Graduation',
        message = (
            f'You have successfully completed the {student.program_type} programme '
            f'and graduated from Semester {student.graduation_semester} '
            f'({student.graduation_year}). '
            f'We wish you all the best for your future. '
            f'Note by HOD: {reason.strip()}'
        )
    ))

    db.session.commit()
    return student, None


# ══════════════════════════════════════════════════════════════════════
#  BULK GRADUATION
#  Graduate ALL students in a department+program_type who are
#  currently at a valid graduation semester.
# ══════════════════════════════════════════════════════════════════════

def bulk_graduate(hod_user, program_type, semester, reason):
    """
    Graduate ALL students in the HOD's department who are at
    the specified semester (which must be a valid graduation semester).

    Used at end-of-year when a whole batch finishes together.

    Returns: dict with graduated/skipped counts and names
    """
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return {'error': 'HOD profile not found.'}

    # Validate that the chosen semester IS a graduation semester
    valid_sems = GRADUATION_RULES.get(program_type, [])
    if semester not in valid_sems:
        valid_str = ' or '.join(str(s) for s in valid_sems)
        return {
            'error': (
                f'Semester {semester} is not a valid graduation semester '
                f'for {program_type}. Valid: Semester {valid_str}.'
            )
        }

    ok, err = _validate_reason(reason)
    if not ok:
        return {'error': err}

    # Fetch all eligible students
    from app.models.user import User
    candidates = (
        Student.query
        .filter_by(
            department_id = hod.department_id,
            program_type  = program_type,
            semester      = semester,
            is_graduated  = False,
        )
        .join(Student.user)
        .filter(User.is_active == True)
        .all()
    )

    if not candidates:
        return {
            'graduated': 0, 'skipped': 0,
            'message': (
                f'No active {program_type} students found at Semester {semester} '
                f'ready for graduation.'
            )
        }

    now             = datetime.utcnow()
    graduated_list  = []
    skipped_list    = []

    for student in candidates:
        # Each student gets individual validation
        # (paranoia check — all should pass given our filter above)
        if student.is_graduated:
            skipped_list.append(f'{student.full_name} (already graduated)')
            continue

        student.is_graduated        = True
        student.graduation_semester = student.semester
        student.graduation_year     = str(now.year)
        student.graduation_reason   = reason.strip()
        student.graduated_at        = now
        student.graduated_by_id     = hod.id
        student.user.is_active      = False

        db.session.add(Notification(
            user_id = student.user_id,
            type    = 'success',
            title   = f'Graduation — {program_type} Batch',
            message = (
                f'Congratulations! You have been graduated as part of the '
                f'{program_type} Semester {semester} batch ({now.year}). '
                f'HOD note: {reason.strip()}'
            )
        ))
        graduated_list.append(student)

    db.session.commit()

    return {
        'graduated'       : len(graduated_list),
        'skipped'         : len(skipped_list),
        'semester'        : semester,
        'program_type'    : program_type,
        'graduated_names' : [s.full_name for s in graduated_list],
        'skipped_names'   : skipped_list,
        'message'         : (
            f'{len(graduated_list)} student(s) graduated from '
            f'{program_type} Semester {semester}. '
            f'{len(skipped_list)} skipped.'
        )
    }


# ══════════════════════════════════════════════════════════════════════
#  READ / QUERY HELPERS
# ══════════════════════════════════════════════════════════════════════

def get_graduated_students(hod_user, program_type=None, year=None):
    """
    Return all graduated students in the HOD's department.
    Optionally filter by program_type or graduation year.
    Ordered by graduation date descending (most recent first).
    """
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return []

    q = Student.query.filter_by(
        department_id=hod.department_id,
        is_graduated=True
    )
    if program_type:
        q = q.filter_by(program_type=program_type)
    if year:
        q = q.filter_by(graduation_year=str(year))

    return q.order_by(Student.graduated_at.desc()).all()


def get_graduation_eligible_students(hod_user):
    """
    Return all students who ARE currently at a valid graduation semester
    but have NOT yet been graduated.

    HOD uses this to see who is ready to graduate today.

    Returns a list of dicts — each with the student and their valid
    graduation semesters — for clear display in the template.
    """
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return []

    from app.models.user import User

    # We can't filter by "semester IN list" cleanly in one SQLAlchemy call
    # across both program types, so we do two queries and combine.
    eligible = []

    for pt, valid_sems in GRADUATION_RULES.items():
        for sem in valid_sems:
            students = (
                Student.query
                .filter_by(
                    department_id=hod.department_id,
                    program_type=pt,
                    semester=sem,
                    is_graduated=False,
                )
                .join(Student.user)
                .filter(User.is_active == True)
                .all()
            )
            for s in students:
                eligible.append({
                    'student'           : s,
                    'valid_semesters'   : valid_sems,
                    'current_semester'  : s.semester,
                    'program_type'      : pt,
                })

    return eligible


def get_graduation_stats(hod_user):
    """
    Summary numbers for the graduation management page.
    """
    hod = Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()
    if not hod:
        return {}

    dept_id = hod.department_id

    total_graduated  = Student.query.filter_by(
        department_id=dept_id, is_graduated=True).count()
    ug_graduated     = Student.query.filter_by(
        department_id=dept_id, is_graduated=True, program_type='UG').count()
    pg_graduated     = Student.query.filter_by(
        department_id=dept_id, is_graduated=True, program_type='PG').count()
    eligible_now     = len(get_graduation_eligible_students(hod_user))

    # Group by year
    from sqlalchemy import func
    year_counts = (
        db.session.query(Student.graduation_year, func.count(Student.id))
        .filter_by(department_id=dept_id, is_graduated=True)
        .group_by(Student.graduation_year)
        .order_by(Student.graduation_year.desc())
        .all()
    )

    return {
        'total_graduated' : total_graduated,
        'ug_graduated'    : ug_graduated,
        'pg_graduated'    : pg_graduated,
        'eligible_now'    : eligible_now,
        'by_year'         : [{'year': y, 'count': c} for y, c in year_counts if y],
    }
