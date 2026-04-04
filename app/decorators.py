# """
# ROLE-BASED ACCESS CONTROL  (RBAC)
# ===================================
# Single source of truth for all access rules in the system.
# Every protected route uses decorators defined here.

# ACCESS CONTROL MATRIX:
#   Action                        Principal  HOD   Teacher  Student
#   ─────────────────────────────────────────────────────────────────
#   Create HOD account               ✅       ❌     ❌       ❌
#   Create Teacher/Student account   ✅       ✅     ❌       ❌
#   Manage departments               ✅       ❌     ❌       ❌
#   View all reports                 ✅       ✅     ❌       ❌
#   Mark attendance                  ❌       ✅     ✅       ❌
#   EDIT attendance                  ❌       ✅     ❌       ❌
#   Promote students (semester)      ❌       ✅     ❌       ❌
#   Graduate students                ❌       ✅     ❌       ❌
#   View own attendance only         ❌       ❌     ❌       ✅
#   View own subjects/timetable      ❌       ❌     ✅       ✅

# THREE LAYERS OF PROTECTION:
#   Layer 1 — Authentication  : is the user logged in and active?
#   Layer 2 — Role check      : does their role allow this action?
#   Layer 3 — Ownership check : do they own THIS specific object?

# DECORATOR STACKING RULE:
#   Flask runs decorators bottom-up (innermost first).
#   Always stack in this order (top to bottom):

#     @blueprint.route('/path')     ← 1. Flask registers URL
#     @login_required               ← 2. Must be logged in
#     @hod_required                 ← 3. Must be HOD
#     @hod_owns_student             ← 4. Must own this student
#     @graduation_not_locked        ← 5. Student must not be graduated
#     def my_view():
#         ...
# """

# from functools import wraps
# from flask import redirect, url_for, flash, abort, request, g
# from flask_login import current_user
# import logging

# access_logger = logging.getLogger('attendance.access')


# # ======================================================================
# #  INTERNAL HELPERS  (private — not imported anywhere)
# # ======================================================================

# def _check_auth():
#     """
#     Checks login AND active status in one step.
#     Returns (True, None) if all good.
#     Returns (False, redirect_response) if we should turn the user away.
#     """
#     if not current_user.is_authenticated:
#         flash('Please log in to access this page.', 'warning')
#         return False, redirect(url_for('auth.login'))
#     if not current_user.is_active:
#         flash('Your account has been deactivated. Contact admin.', 'danger')
#         return False, redirect(url_for('auth.logout'))
#     return True, None


# def _deny(message: str):
#     """
#     Log the blocked attempt, flash a message, and send a 403 response.
#     Using abort(403) means Flask's registered 403 error handler runs —
#     the user sees our custom error page, not a raw HTTP error.
#     """
#     access_logger.warning(
#         'ACCESS DENIED | user=%s | role=%s | path=%s',
#         getattr(current_user, 'email', 'anonymous'),
#         getattr(current_user, 'role',  'none'),
#         request.path
#     )
#     flash(message, 'danger')
#     abort(403)


# # ======================================================================
# #  LAYER 2 — ROLE DECORATORS
# # ======================================================================

# def principal_required(f):
#     """
#     ONLY the Principal can pass.

#     Correct usage:
#         @principal_bp.route('/create-hod')
#         @login_required
#         @principal_required
#         def create_hod():
#             ...  # only runs if user is Principal

#     What happens if a Teacher hits this route?
#         → _deny() is called → 403 page shown → route never runs
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         ok, resp = _check_auth()
#         if not ok:
#             return resp
#         if not current_user.is_principal:
#             _deny('Only the Principal can access this area.')
#         return f(*args, **kwargs)
#     return decorated


# def hod_required(f):
#     """
#     ONLY the HOD can pass.

#     Key actions behind this guard:
#       - Edit attendance records     (with mandatory reason)
#       - Promote students semester-wise
#       - Graduate students
#       - Manage department teachers

#     Correct usage:
#         @hod_bp.route('/attendance/<int:attendance_id>/edit')
#         @login_required
#         @hod_required
#         def edit_attendance(attendance_id):
#             ...

#     What happens if a Teacher hits this route?
#         → "Only the HOD can perform this action." + 403
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         ok, resp = _check_auth()
#         if not ok:
#             return resp
#         if not current_user.is_hod:
#             _deny('Only the HOD can perform this action.')
#         return f(*args, **kwargs)
#     return decorated


# def teacher_required(f):
#     """
#     Teachers AND HODs can pass.
#     HOD inherits all teacher permissions — they can mark attendance
#     for any class in their department.

#     Correct usage:
#         @teacher_bp.route('/attendance/mark/<int:subject_id>')
#         @login_required
#         @teacher_required
#         def mark_attendance(subject_id):
#             ...

#     What happens if a Student hits this route?
#         → "Only teachers can access this area." + 403
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         ok, resp = _check_auth()
#         if not ok:
#             return resp
#         if not (current_user.is_teacher or current_user.is_hod):
#             _deny('Only teachers can access this area.')
#         return f(*args, **kwargs)
#     return decorated


# def student_required(f):
#     """
#     ONLY a Student can pass.

#     Correct usage:
#         @student_bp.route('/my-attendance')
#         @login_required
#         @student_required
#         def my_attendance():
#             ...
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         ok, resp = _check_auth()
#         if not ok:
#             return resp
#         if not current_user.is_student:
#             _deny('Only students can access this area.')
#         return f(*args, **kwargs)
#     return decorated


# def principal_or_hod_required(f):
#     """
#     Principal OR HOD can pass.

#     Used for:
#       - Creating teacher accounts
#       - Creating student accounts
#       - Managing subjects

#     Why both?
#       Principal manages the whole college.
#       HOD manages their own department.
#       Both need the ability to add people.
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         ok, resp = _check_auth()
#         if not ok:
#             return resp
#         if not (current_user.is_principal or current_user.is_hod):
#             _deny('Only Principal or HOD can access this area.')
#         return f(*args, **kwargs)
#     return decorated


# def role_required(*roles):
#     """
#     Generic decorator — accepts any combination of role strings.
#     Prefer the named decorators above for readability.

#     Usage:
#         @role_required('principal', 'hod')
#         def some_view(): ...

#         @role_required('teacher')
#         def another_view(): ...
#     """
#     def decorator(f):
#         @wraps(f)
#         def decorated_function(*args, **kwargs):
#             ok, resp = _check_auth()
#             if not ok:
#                 return resp
#             if current_user.role not in roles:
#                 _deny(
#                     f'Access requires one of: {", ".join(roles)}. '
#                     f'You are logged in as: {current_user.role}.'
#                 )
#             return f(*args, **kwargs)
#         return decorated_function
#     return decorator


# # ======================================================================
# #  LAYER 3 — OBJECT-LEVEL OWNERSHIP GUARDS
# #  These answer: "not just CAN you do this, but do you OWN this object?"
# # ======================================================================

# def hod_owns_student(f):
#     """
#     HOD can only act on students in THEIR OWN department.

#     Why this matters:
#         Without this guard, the HOD of CSE could visit:
#           /hod/student/42/promote
#         and promote a student from the ECE department.
#         That is a data integrity violation.

#     This decorator:
#       1. Fetches the Student from the DB
#       2. Compares student.department_id with hod.department_id
#       3. Denies if they don't match
#       4. Saves the fetched student in g.owned_student so the
#          route doesn't need to query the DB again

#     Route MUST have 'student_id' in its URL:
#         @hod_bp.route('/student/<int:student_id>/promote')
#         @login_required
#         @hod_required
#         @hod_owns_student
#         def promote_student(student_id):
#             student = g.owned_student   ← already fetched
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         from app.models import Student
#         student_id = kwargs.get('student_id')
#         if student_id is None:
#             abort(400)

#         student    = Student.query.get_or_404(student_id)
#         hod_teacher = current_user.teacher_profile

#         if not hod_teacher:
#             _deny('HOD teacher profile not found. Contact admin.')

#         if student.department_id != hod_teacher.department_id:
#             _deny('You can only manage students in your own department.')

#         g.owned_student = student
#         return f(*args, **kwargs)
#     return decorated


# def hod_owns_attendance(f):
#     """
#     HOD can only EDIT attendance records that belong to students
#     in their own department.

#     Why this matters:
#         Attendance editing is a sensitive operation — it changes
#         a student's academic record. We must ensure the HOD can
#         only touch records in their own department.

#     This decorator also verifies that the edit includes a reason,
#     which is enforced at the service layer (not here).

#     Route MUST have 'attendance_id' in its URL:
#         @hod_bp.route('/attendance/<int:attendance_id>/edit')
#         @login_required
#         @hod_required
#         @hod_owns_attendance
#         def edit_attendance(attendance_id):
#             record = g.owned_attendance
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         from app.models import Attendance
#         attendance_id = kwargs.get('attendance_id')
#         if attendance_id is None:
#             abort(400)

#         record      = Attendance.query.get_or_404(attendance_id)
#         hod_teacher  = current_user.teacher_profile

#         if not hod_teacher:
#             _deny('HOD teacher profile not found.')

#         if record.student.department_id != hod_teacher.department_id:
#             _deny('You can only edit attendance for your own department.')

#         g.owned_attendance = record
#         return f(*args, **kwargs)
#     return decorated


# def teacher_owns_subject(f):
#     """
#     A teacher can only mark attendance for subjects ASSIGNED to them.

#     Why this matters:
#         Without this, Teacher A could submit attendance for Teacher B's
#         class — a serious academic integrity violation.

#     HOD exception:
#         The HOD can mark attendance for ANY subject in their department
#         (useful when a teacher is absent).

#     Route MUST have 'subject_id' in its URL:
#         @teacher_bp.route('/mark/<int:subject_id>')
#         @login_required
#         @teacher_required
#         @teacher_owns_subject
#         def mark(subject_id):
#             subject = g.owned_subject
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         from app.models import Subject
#         subject_id = kwargs.get('subject_id')
#         if subject_id is None:
#             abort(400)

#         subject = Subject.query.get_or_404(subject_id)
#         teacher = current_user.teacher_profile

#         if not teacher:
#             _deny('Teacher profile not found.')

#         # HOD override — can cover any subject in their department
#         if current_user.is_hod:
#             if subject.department_id != teacher.department_id:
#                 _deny('Subject is not in your department.')
#             g.owned_subject = subject
#             return f(*args, **kwargs)

#         # Regular teacher — must be explicitly assigned
#         assigned_ids = [s.id for s in teacher.subjects.all()]
#         if subject.id not in assigned_ids:
#             _deny('You are not assigned to teach this subject.')

#         g.owned_subject = subject
#         return f(*args, **kwargs)
#     return decorated


# def student_owns_record(f):
#     """
#     Students can only VIEW their own attendance data.

#     Why this matters:
#         Student A must never see Student B's records.
#         Even if Student A guesses Student B's ID in the URL,
#         this guard stops them.

#     Route MUST have 'student_id' in its URL:
#         @student_bp.route('/attendance/<int:student_id>')
#         @login_required
#         @student_required
#         @student_owns_record
#         def view_attendance(student_id):
#             student = g.owned_student
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         from app.models import Student
#         student_id  = kwargs.get('student_id')
#         if student_id is None:
#             abort(400)

#         student    = Student.query.get_or_404(student_id)
#         own_profile = current_user.student_profile

#         if not own_profile or own_profile.id != student.id:
#             _deny('You can only view your own attendance records.')

#         g.owned_student = student
#         return f(*args, **kwargs)
#     return decorated


# # ======================================================================
# #  SPECIAL BUSINESS-RULE GUARDS
# #  These enforce the core rules of the graduation system.
# # ======================================================================

# def graduation_not_locked(f):
#     """
#     Blocks any action on a GRADUATED student.

#     Graduated students are permanently frozen:
#       - Cannot be promoted further
#       - Cannot be re-graduated
#       - Their data is read-only

#     Must come AFTER @hod_owns_student (so g.owned_student is set).

#     Usage:
#         @hod_bp.route('/student/<int:student_id>/promote')
#         @login_required
#         @hod_required
#         @hod_owns_student
#         @graduation_not_locked
#         def promote_student(student_id):
#             ...
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         student = getattr(g, 'owned_student', None)
#         if student is None:
#             from app.models import Student
#             student = Student.query.get_or_404(kwargs.get('student_id'))

#         if student.is_graduated:
#             flash(
#                 f'{student.full_name} has already graduated '
#                 f'(Sem {student.graduation_semester}, {student.graduation_year}). '
#                 f'Graduated students cannot be modified.',
#                 'warning'
#             )
#             return redirect(url_for('hod.dashboard'))

#         return f(*args, **kwargs)
#     return decorated


# def can_graduate_check(f):
#     """
#     Verifies the student has REACHED a valid graduation semester.

#     UG → must be at semester 6 or 8
#     PG → must be at semester 4

#     Graduation is time-independent and manually controlled by HOD.
#     This guard just verifies the semester precondition is met.

#     Must come AFTER @hod_owns_student AND @graduation_not_locked.
#     """
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         student = getattr(g, 'owned_student', None)
#         if student is None:
#             from app.models import Student
#             student = Student.query.get_or_404(kwargs.get('student_id'))

#         if not student.can_be_graduated:
#             flash(
#                 f'Cannot graduate {student.full_name}. '
#                 f'Currently at Semester {student.semester}. '
#                 f'{student.program_type} students can graduate at: '
#                 f'Semester {", ".join(str(s) for s in student.valid_graduation_semesters)}.',
#                 'warning'
#             )
#             return redirect(url_for('hod.dashboard'))

#         return f(*args, **kwargs)
#     return decorated

##################--------------updated----------------
"""
ROLE-BASED ACCESS CONTROL  (RBAC)
===================================
Single source of truth for all access rules in the system.
Every protected route uses decorators defined here.

ACCESS CONTROL MATRIX:
  Action                        Principal  HOD   Teacher  Student
  ─────────────────────────────────────────────────────────────────
  Create HOD account               ✅       ❌     ❌       ❌
  Create Teacher/Student account   ✅       ✅     ❌       ❌
  Manage departments               ✅       ❌     ❌       ❌
  View all reports                 ✅       ✅     ❌       ❌
  Mark attendance                  ❌       ✅     ✅       ❌
  EDIT attendance                  ❌       ✅     ❌       ❌
  Promote students (semester)      ❌       ✅     ❌       ❌
  Graduate students                ❌       ✅     ❌       ❌
  View own attendance only         ❌       ❌     ❌       ✅
  View own subjects/timetable      ❌       ❌     ✅       ✅

THREE LAYERS OF PROTECTION:
  Layer 1 — Authentication  : is the user logged in and active?
  Layer 2 — Role check      : does their role allow this action?
  Layer 3 — Ownership check : do they own THIS specific object?

DECORATOR STACKING RULE:
  Flask runs decorators bottom-up (innermost first).
  Always stack in this order (top to bottom):

    @blueprint.route('/path')     ← 1. Flask registers URL
    @login_required               ← 2. Must be logged in
    @hod_required                 ← 3. Must be HOD
    @hod_owns_student             ← 4. Must own this student
    @graduation_not_locked        ← 5. Student must not be graduated
    def my_view():
        ...
"""

from functools import wraps
from flask import redirect, url_for, flash, abort, request, g
from flask_login import current_user
import logging

access_logger = logging.getLogger('attendance.access')


# ======================================================================
#  INTERNAL HELPERS  (private — not imported anywhere)
# ======================================================================

def _check_auth():
    """
    Checks login AND active status in one step.
    Returns (True, None) if all good.
    Returns (False, redirect_response) if we should turn the user away.
    """
    if not current_user.is_authenticated:
        flash('Please log in to access this page.', 'warning')
        return False, redirect(url_for('auth.login'))
    if not current_user.is_active:
        flash('Your account has been deactivated. Contact admin.', 'danger')
        return False, redirect(url_for('auth.logout'))
    return True, None


def _deny(message: str):
    """
    Log the blocked attempt, flash a message, and send a 403 response.
    Using abort(403) means Flask's registered 403 error handler runs —
    the user sees our custom error page, not a raw HTTP error.
    """
    access_logger.warning(
        'ACCESS DENIED | user=%s | role=%s | path=%s',
        getattr(current_user, 'email', 'anonymous'),
        getattr(current_user, 'role',  'none'),
        request.path
    )
    flash(message, 'danger')
    abort(403)


# ======================================================================
#  LAYER 2 — ROLE DECORATORS
# ======================================================================

def principal_required(f):
    """
    ONLY the Principal can pass.

    Correct usage:
        @principal_bp.route('/create-hod')
        @login_required
        @principal_required
        def create_hod():
            ...  # only runs if user is Principal

    What happens if a Teacher hits this route?
        → _deny() is called → 403 page shown → route never runs
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        ok, resp = _check_auth()
        if not ok:
            return resp
        if not current_user.is_principal:
            _deny('Only the Principal can access this area.')
        return f(*args, **kwargs)
    return decorated


def hod_required(f):
    """
    ONLY the HOD can pass.

    Key actions behind this guard:
      - Edit attendance records     (with mandatory reason)
      - Promote students semester-wise
      - Graduate students
      - Manage department teachers

    Correct usage:
        @hod_bp.route('/attendance/<int:attendance_id>/edit')
        @login_required
        @hod_required
        def edit_attendance(attendance_id):
            ...

    What happens if a Teacher hits this route?
        → "Only the HOD can perform this action." + 403
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        ok, resp = _check_auth()
        if not ok:
            return resp
        if not current_user.is_hod:
            _deny('Only the HOD can perform this action.')
        return f(*args, **kwargs)
    return decorated


def teacher_required(f):
    """
    Teachers AND HODs can pass.
    HOD inherits all teacher permissions — they can mark attendance
    for any class in their department.

    Correct usage:
        @teacher_bp.route('/attendance/mark/<int:subject_id>')
        @login_required
        @teacher_required
        def mark_attendance(subject_id):
            ...

    What happens if a Student hits this route?
        → "Only teachers can access this area." + 403
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        ok, resp = _check_auth()
        if not ok:
            return resp
        if not (current_user.is_teacher or current_user.is_hod):
            _deny('Only teachers can access this area.')
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    """
    ONLY a Student can pass.

    Correct usage:
        @student_bp.route('/my-attendance')
        @login_required
        @student_required
        def my_attendance():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        ok, resp = _check_auth()
        if not ok:
            return resp
        if not current_user.is_student:
            _deny('Only students can access this area.')
        return f(*args, **kwargs)
    return decorated


def principal_or_hod_required(f):
    """
    Principal OR HOD can pass.

    Used for:
      - Creating teacher accounts
      - Creating student accounts
      - Managing subjects

    Why both?
      Principal manages the whole college.
      HOD manages their own department.
      Both need the ability to add people.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        ok, resp = _check_auth()
        if not ok:
            return resp
        if not (current_user.is_principal or current_user.is_hod):
            _deny('Only Principal or HOD can access this area.')
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    """
    Generic decorator — accepts any combination of role strings.
    Prefer the named decorators above for readability.

    Usage:
        @role_required('principal', 'hod')
        def some_view(): ...

        @role_required('teacher')
        def another_view(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ok, resp = _check_auth()
            if not ok:
                return resp
            if current_user.role not in roles:
                _deny(
                    f'Access requires one of: {", ".join(roles)}. '
                    f'You are logged in as: {current_user.role}.'
                )
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ======================================================================
#  LAYER 3 — OBJECT-LEVEL OWNERSHIP GUARDS
#  These answer: "not just CAN you do this, but do you OWN this object?"
# ======================================================================

def hod_owns_student(f):
    """
    HOD can only act on students in THEIR OWN department.

    Why this matters:
        Without this guard, the HOD of CSE could visit:
          /hod/student/42/promote
        and promote a student from the ECE department.
        That is a data integrity violation.

    This decorator:
      1. Fetches the Student from the DB
      2. Compares student.department_id with hod.department_id
      3. Denies if they don't match
      4. Saves the fetched student in g.owned_student so the
         route doesn't need to query the DB again

    Route MUST have 'student_id' in its URL:
        @hod_bp.route('/student/<int:student_id>/promote')
        @login_required
        @hod_required
        @hod_owns_student
        def promote_student(student_id):
            student = g.owned_student   ← already fetched
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.models.student import Student
        student_id = kwargs.get('student_id')
        if student_id is None:
            abort(400)

        student    = Student.query.get_or_404(student_id)
        hod_teacher = current_user.teacher_profile

        if not hod_teacher:
            _deny('HOD teacher profile not found. Contact admin.')

        if student.department_id != hod_teacher.department_id:
            _deny('You can only manage students in your own department.')

        g.owned_student = student
        return f(*args, **kwargs)
    return decorated


def hod_owns_attendance(f):
    """
    HOD can only EDIT attendance records that belong to students
    in their own department.

    Why this matters:
        Attendance editing is a sensitive operation — it changes
        a student's academic record. We must ensure the HOD can
        only touch records in their own department.

    This decorator also verifies that the edit includes a reason,
    which is enforced at the service layer (not here).

    Route MUST have 'attendance_id' in its URL:
        @hod_bp.route('/attendance/<int:attendance_id>/edit')
        @login_required
        @hod_required
        @hod_owns_attendance
        def edit_attendance(attendance_id):
            record = g.owned_attendance
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.models import Attendance
        attendance_id = kwargs.get('attendance_id')
        if attendance_id is None:
            abort(400)

        record      = Attendance.query.get_or_404(attendance_id)
        hod_teacher  = current_user.teacher_profile

        if not hod_teacher:
            _deny('HOD teacher profile not found.')

        if record.student.department_id != hod_teacher.department_id:
            _deny('You can only edit attendance for your own department.')

        g.owned_attendance = record
        return f(*args, **kwargs)
    return decorated


def teacher_owns_subject(f):
    """
    A teacher can only mark attendance for subjects ASSIGNED to them.

    Why this matters:
        Without this, Teacher A could submit attendance for Teacher B's
        class — a serious academic integrity violation.

    HOD exception:
        The HOD can mark attendance for ANY subject in their department
        (useful when a teacher is absent).

    Route MUST have 'subject_id' in its URL:
        @teacher_bp.route('/mark/<int:subject_id>')
        @login_required
        @teacher_required
        @teacher_owns_subject
        def mark(subject_id):
            subject = g.owned_subject
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.models.subject import Subject
        subject_id = kwargs.get('subject_id')
        if subject_id is None:
            abort(400)

        subject = Subject.query.get_or_404(subject_id)
        teacher = current_user.teacher_profile

        if not teacher:
            _deny('Teacher profile not found.')

        # HOD override — can cover any subject in their department
        if current_user.is_hod:
            if subject.department_id != teacher.department_id:
                _deny('Subject is not in your department.')
            g.owned_subject = subject
            return f(*args, **kwargs)

        # Regular teacher — must be explicitly assigned
        assigned_ids = [s.id for s in teacher.subjects.all()]
        if subject.id not in assigned_ids:
            _deny('You are not assigned to teach this subject.')

        g.owned_subject = subject
        return f(*args, **kwargs)
    return decorated


def student_owns_record(f):
    """
    Students can only VIEW their own attendance data.

    Why this matters:
        Student A must never see Student B's records.
        Even if Student A guesses Student B's ID in the URL,
        this guard stops them.

    Route MUST have 'student_id' in its URL:
        @student_bp.route('/attendance/<int:student_id>')
        @login_required
        @student_required
        @student_owns_record
        def view_attendance(student_id):
            student = g.owned_student
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.models.student import Student
        student_id  = kwargs.get('student_id')
        if student_id is None:
            abort(400)

        student    = Student.query.get_or_404(student_id)
        own_profile = current_user.student_profile

        if not own_profile or own_profile.id != student.id:
            _deny('You can only view your own attendance records.')

        g.owned_student = student
        return f(*args, **kwargs)
    return decorated


# ======================================================================
#  SPECIAL BUSINESS-RULE GUARDS
#  These enforce the core rules of the graduation system.
# ======================================================================

def graduation_not_locked(f):
    """
    Blocks any action on a GRADUATED student.

    Graduated students are permanently frozen:
      - Cannot be promoted further
      - Cannot be re-graduated
      - Their data is read-only

    Must come AFTER @hod_owns_student (so g.owned_student is set).

    Usage:
        @hod_bp.route('/student/<int:student_id>/promote')
        @login_required
        @hod_required
        @hod_owns_student
        @graduation_not_locked
        def promote_student(student_id):
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        student = getattr(g, 'owned_student', None)
        if student is None:
            from app.models import Student
            student = Student.query.get_or_404(kwargs.get('student_id'))

        if student.is_graduated:
            flash(
                f'{student.full_name} has already graduated '
                f'(Sem {student.graduation_semester}, {student.graduation_year}). '
                f'Graduated students cannot be modified.',
                'warning'
            )
            return redirect(url_for('hod.dashboard'))

        return f(*args, **kwargs)
    return decorated


def can_graduate_check(f):
    """
    Verifies the student has REACHED a valid graduation semester.

    UG → must be at semester 6 or 8
    PG → must be at semester 4

    Graduation is time-independent and manually controlled by HOD.
    This guard just verifies the semester precondition is met.

    Must come AFTER @hod_owns_student AND @graduation_not_locked.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        student = getattr(g, 'owned_student', None)
        if student is None:
            from app.models import Student
            student = Student.query.get_or_404(kwargs.get('student_id'))

        if not student.can_be_graduated:
            flash(
                f'Cannot graduate {student.full_name}. '
                f'Currently at Semester {student.semester}. '
                f'{student.program_type} students can graduate at: '
                f'Semester {", ".join(str(s) for s in student.valid_graduation_semesters)}.',
                'warning'
            )
            return redirect(url_for('hod.dashboard'))

        return f(*args, **kwargs)
    return decorated