"""
HOD SERVICE
===========
All business logic for the HOD dashboard.
Covers: Teacher CRUD, Subject CRUD, Student management,
        Semester promotion (single + bulk), Deletion with reason.

Design rules enforced here (NOT in routes):
  1. HOD can only manage objects inside THEIR OWN department.
  2. Graduated students are frozen — no edits, no promotion.
  3. Promotion is one semester at a time (no skipping).
  4. Bulk promotion moves ALL students of a given semester — but
     skips anyone already at max or already graduated.
  5. Deletion is always SOFT — we deactivate, never hard-delete.
     Academic records must be preserved forever.
"""

from datetime import datetime
from app import db
from app.models.user        import User, Role
from app.models.teacher     import Teacher
from app.models.student     import Student
from app.models.subject     import Subject
from app.models.department  import Department
from app.models.notification import Notification


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════

def _get_hod_teacher(hod_user):
    """
    Given the logged-in HOD User, return their Teacher profile.
    Returns None if somehow a non-teacher user calls an HOD action.
    """
    return Teacher.query.filter_by(user_id=hod_user.id, is_hod=True).first()


def _assert_same_dept(obj_dept_id, hod_dept_id, label='Object'):
    """
    Safety check — ensure the HOD is acting on something in THEIR department.
    Returns (True, None) if OK, (False, error_msg) if cross-dept.
    """
    if obj_dept_id != hod_dept_id:
        return False, f'{label} does not belong to your department.'
    return True, None


# ══════════════════════════════════════════════════════════════════════
#  TEACHER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

def create_teacher(hod_user, first_name, last_name, email,
                   password, employee_id):
    """
    Create a new Teacher account inside the HOD's department.

    Two DB writes, one transaction:
      1. User row  — login credentials, role='teacher'
      2. Teacher row — department_id, employee_id

    Returns: (user, None) | (None, error_msg)
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return None, 'HOD profile not found.'

    email       = email.strip().lower()
    employee_id = employee_id.strip().upper()

    if not all([first_name, last_name, email, password, employee_id]):
        return None, 'All fields are required.'
    if len(password) < 8:
        return None, 'Password must be at least 8 characters.'
    if User.query.filter_by(email=email).first():
        return None, f'Email "{email}" is already registered.'
    if Teacher.query.filter_by(employee_id=employee_id).first():
        return None, f'Employee ID "{employee_id}" is already in use.'

    user = User(
        email=email, first_name=first_name.strip(),
        last_name=last_name.strip(), role=Role.TEACHER
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    teacher = Teacher(
        user_id=user.id,
        department_id=hod.department_id,
        employee_id=employee_id,
        is_hod=False
    )
    db.session.add(teacher)
    db.session.commit()

    # Welcome notification
    db.session.add(Notification(
        user_id=user.id, type='info',
        title='Welcome to the team',
        message=f'Your teacher account has been created for '
                f'{hod.department.name} department.'
    ))
    db.session.commit()
    return user, None


def update_teacher(hod_user, teacher_id, first_name, last_name, employee_id):
    """
    Update a teacher's personal details (not password, not department).
    HOD can only edit teachers in their own department.

    Returns: (teacher, None) | (None, error_msg)
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return None, 'HOD profile not found.'

    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return None, 'Teacher not found.'

    ok, err = _assert_same_dept(teacher.department_id, hod.department_id, 'Teacher')
    if not ok:
        return None, err

    # Check employee_id uniqueness (exclude current teacher)
    clash = Teacher.query.filter(
        Teacher.employee_id == employee_id.strip().upper(),
        Teacher.id != teacher_id
    ).first()
    if clash:
        return None, f'Employee ID "{employee_id}" is already in use.'

    teacher.employee_id    = employee_id.strip().upper()
    teacher.user.first_name = first_name.strip()
    teacher.user.last_name  = last_name.strip()
    db.session.commit()
    return teacher, None


def deactivate_teacher(hod_user, teacher_id):
    """
    Soft-delete a teacher (set is_active=False on both Teacher and User).
    We never hard-delete — attendance records they marked must remain.

    Returns: (True, None) | (False, error_msg)
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return False, 'HOD profile not found.'

    teacher = Teacher.query.get(teacher_id)
    if not teacher:
        return False, 'Teacher not found.'

    if teacher.is_hod:
        return False, 'Cannot deactivate an HOD through this action. Contact the Principal.'

    ok, err = _assert_same_dept(teacher.department_id, hod.department_id, 'Teacher')
    if not ok:
        return False, err

    teacher.is_active      = False
    teacher.user.is_active  = False
    db.session.commit()
    return True, None


def get_dept_teachers(hod_user, include_inactive=False):
    """
    Return all teachers in the HOD's department.
    By default, only active non-HOD teachers are returned.
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return []

    q = Teacher.query.filter_by(
        department_id=hod.department_id,
        is_hod=False
    )
    if not include_inactive:
        q = q.filter_by(is_active=True)
    return q.all()


def assign_subject_to_teacher(hod_user, teacher_id, subject_id):
    """
    Link a teacher to a subject (many-to-many via teacher_subjects table).
    HOD can only assign subjects and teachers from their own department.

    Returns: (True, None) | (False, error_msg)
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return False, 'HOD profile not found.'

    teacher = Teacher.query.get(teacher_id)
    subject = Subject.query.get(subject_id)

    if not teacher or not subject:
        return False, 'Teacher or subject not found.'

    ok, err = _assert_same_dept(teacher.department_id, hod.department_id, 'Teacher')
    if not ok:
        return False, err
    ok, err = _assert_same_dept(subject.department_id, hod.department_id, 'Subject')
    if not ok:
        return False, err

    # Check: already assigned?
    if subject in teacher.subjects.all():
        return False, f'{teacher.full_name} is already assigned to {subject.name}.'

    teacher.subjects.append(subject)
    db.session.commit()
    return True, None


def unassign_subject_from_teacher(hod_user, teacher_id, subject_id):
    """Remove a subject assignment from a teacher."""
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return False, 'HOD profile not found.'

    teacher = Teacher.query.get(teacher_id)
    subject = Subject.query.get(subject_id)
    if not teacher or not subject:
        return False, 'Teacher or subject not found.'

    ok, err = _assert_same_dept(teacher.department_id, hod.department_id, 'Teacher')
    if not ok:
        return False, err

    if subject not in teacher.subjects.all():
        return False, f'{teacher.full_name} is not assigned to {subject.name}.'

    teacher.subjects.remove(subject)
    db.session.commit()
    return True, None


# ══════════════════════════════════════════════════════════════════════
#  SUBJECT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

def create_subject(hod_user, name, code, semester, program_type, total_classes):
    """
    Create a new subject inside the HOD's department.

    Returns: (subject, None) | (None, error_msg)
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return None, 'HOD profile not found.'

    name = name.strip()
    code = code.strip().upper()

    if not name or not code:
        return None, 'Subject name and code are required.'

    # Validate semester range based on program_type
    max_sem = 8 if program_type == 'UG' else 4
    if not (1 <= semester <= max_sem):
        return None, f'{program_type} semester must be between 1 and {max_sem}.'

    if Subject.query.filter_by(code=code).first():
        return None, f'Subject code "{code}" is already in use.'

    try:
        total_classes = int(total_classes)
        if total_classes < 1:
            raise ValueError
    except (ValueError, TypeError):
        return None, 'Total classes must be a positive number.'

    subject = Subject(
        department_id=hod.department_id,
        name=name, code=code,
        semester=semester, program_type=program_type,
        total_classes=total_classes
    )
    db.session.add(subject)
    db.session.commit()
    return subject, None


def update_subject(hod_user, subject_id, name, code, semester,
                   program_type, total_classes):
    """Update an existing subject's details."""
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return None, 'HOD profile not found.'

    subject = Subject.query.get(subject_id)
    if not subject:
        return None, 'Subject not found.'

    ok, err = _assert_same_dept(subject.department_id, hod.department_id, 'Subject')
    if not ok:
        return None, err

    code = code.strip().upper()
    clash = Subject.query.filter(
        Subject.code == code, Subject.id != subject_id
    ).first()
    if clash:
        return None, f'Subject code "{code}" is already in use.'

    max_sem = 8 if program_type == 'UG' else 4
    if not (1 <= semester <= max_sem):
        return None, f'{program_type} semester must be between 1 and {max_sem}.'

    subject.name          = name.strip()
    subject.code          = code
    subject.semester      = semester
    subject.program_type  = program_type
    subject.total_classes = int(total_classes)
    db.session.commit()
    return subject, None


def deactivate_subject(hod_user, subject_id):
    """
    Soft-delete a subject.
    Cannot delete if attendance records exist — those must be preserved.

    Returns: (True, None) | (False, error_msg)
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return False, 'HOD profile not found.'

    subject = Subject.query.get(subject_id)
    if not subject:
        return False, 'Subject not found.'

    ok, err = _assert_same_dept(subject.department_id, hod.department_id, 'Subject')
    if not ok:
        return False, err

    if subject.attendance_records.count() > 0:
        return False, (
            f'Cannot deactivate "{subject.name}": '
            f'{subject.attendance_records.count()} attendance records exist. '
            f'These are preserved for academic records.'
        )

    subject.is_active = False
    db.session.commit()
    return True, None


def get_dept_subjects(hod_user, semester=None, program_type=None):
    """
    Return subjects in the HOD's department.
    Optionally filter by semester and/or program_type.
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return []

    q = Subject.query.filter_by(
        department_id=hod.department_id,
        is_active=True
    )
    if semester:
        q = q.filter_by(semester=semester)
    if program_type:
        q = q.filter_by(program_type=program_type)

    return q.order_by(Subject.semester, Subject.name).all()


# ══════════════════════════════════════════════════════════════════════
#  STUDENT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

def create_student(hod_user, first_name, last_name, email, password,
                   roll_number, admission_year, program_type, semester=1):
    """
    Create a new student account inside the HOD's department.

    Returns: (user, None) | (None, error_msg)
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return None, 'HOD profile not found.'

    email       = email.strip().lower()
    roll_number = roll_number.strip().upper()

    if not all([first_name, last_name, email, password, roll_number, admission_year]):
        return None, 'All fields are required.'
    if len(password) < 8:
        return None, 'Password must be at least 8 characters.'
    if User.query.filter_by(email=email).first():
        return None, f'Email "{email}" is already registered.'
    if Student.query.filter_by(roll_number=roll_number).first():
        return None, f'Roll number "{roll_number}" is already in use.'
    if program_type not in ('UG', 'PG'):
        return None, 'Program type must be UG or PG.'

    max_sem = 8 if program_type == 'UG' else 4
    if not (1 <= semester <= max_sem):
        return None, f'Semester must be 1–{max_sem} for {program_type}.'

    user = User(
        email=email, first_name=first_name.strip(),
        last_name=last_name.strip(), role=Role.STUDENT
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    student = Student(
        user_id=user.id,
        department_id=hod.department_id,
        roll_number=roll_number,
        admission_year=admission_year.strip(),
        program_type=program_type,
        semester=semester
    )
    db.session.add(student)
    db.session.commit()

    db.session.add(Notification(
        user_id=user.id, type='success',
        title='Enrollment Confirmed',
        message=f'Welcome! You are enrolled in Semester {semester} '
                f'({program_type}) at {hod.department.name}.'
    ))
    db.session.commit()
    return user, None


def soft_delete_student(hod_user, student_id, reason):
    """
    Soft-delete (deactivate) a student WITH a mandatory reason.

    WHY soft-delete only?
      Deleting a student would destroy all their attendance records —
      which are academic evidence. We just deactivate their login.
      The data stays; the person can no longer log in.

    The reason is stored so there's a clear audit trail of who
    removed whom and why.

    Returns: (True, None) | (False, error_msg)
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return False, 'HOD profile not found.'

    if not reason or len(reason.strip()) < 5:
        return False, 'A reason of at least 5 characters is required.'

    student = Student.query.get(student_id)
    if not student:
        return False, 'Student not found.'

    ok, err = _assert_same_dept(student.department_id, hod.department_id, 'Student')
    if not ok:
        return False, err

    if student.is_graduated:
        return False, 'Graduated students are already inactive.'

    # Already soft-deleted?
    if not student.user.is_active:
        return False, f"{student.full_name} is already deactivated."

    # Deactivate login
    student.user.is_active = False

    # Store reason in graduation_reason field (repurposed for deletion notes)
    student.graduation_reason = f'[REMOVED] {reason.strip()}'
    student.graduated_at      = datetime.utcnow()
    student.graduated_by_id   = hod.id

    db.session.commit()

    # Notify the student (they can still read notifs even if inactive? No —
    # but we keep the record for admin auditing purposes)
    db.session.add(Notification(
        user_id=student.user_id, type='danger',
        title='Account Deactivated',
        message=f'Your student account has been deactivated. Reason: {reason.strip()}'
    ))
    db.session.commit()
    return True, None


def get_students_by_semester(hod_user, semester=None, program_type=None,
                              include_graduated=False):
    """
    Return students in the HOD's department.
    Optionally filter by semester and/or program_type.

    Default: only active (non-graduated) students.
    Set include_graduated=True to also show alumni.
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return []

    q = Student.query.filter_by(department_id=hod.department_id)

    if not include_graduated:
        q = q.filter_by(is_graduated=False)

    # Also exclude soft-deleted (user.is_active=False but not graduated)
    q = q.join(Student.user).filter(User.is_active == True)

    if semester:
        q = q.filter(Student.semester == semester)
    if program_type:
        q = q.filter(Student.program_type == program_type)

    return q.order_by(Student.semester, Student.roll_number).all()


# ══════════════════════════════════════════════════════════════════════
#  SEMESTER PROMOTION
# ══════════════════════════════════════════════════════════════════════

def promote_single_student(hod_user, student_id):
    """
    Promote ONE student to the next semester.

    Rules enforced:
      1. Student must be in HOD's department.
      2. Student must NOT be graduated.
      3. Student must NOT already be at max semester.
         (UG max = 8, PG max = 4)
      4. One promotion at a time — no skipping semesters.

    Returns: (student, None) | (None, error_msg)
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return None, 'HOD profile not found.'

    student = Student.query.get(student_id)
    if not student:
        return None, 'Student not found.'

    ok, err = _assert_same_dept(student.department_id, hod.department_id, 'Student')
    if not ok:
        return None, err

    # Rule 2: graduated students are frozen
    if student.is_graduated:
        return None, (
            f'{student.full_name} has already graduated '
            f'(Sem {student.graduation_semester}). Cannot promote.'
        )

    # Rule 3: already at max?
    if student.semester >= student.max_semester:
        return None, (
            f'{student.full_name} is already at the maximum semester '
            f'({student.max_semester}) for {student.program_type}.'
        )

    old_sem          = student.semester
    student.semester += 1               # Rule 4: exactly +1, never more
    db.session.commit()

    # Notify student
    db.session.add(Notification(
        user_id=student.user_id, type='success',
        title='Semester Promotion',
        message=f'Congratulations! You have been promoted from '
                f'Semester {old_sem} to Semester {student.semester}.'
    ))
    db.session.commit()
    return student, None


def bulk_promote(hod_user, from_semester, program_type):
    """
    Promote ALL eligible students from from_semester → from_semester+1
    within the HOD's department and specified program_type.

    DOUBLE PROMOTION PREVENTION:
    ─────────────────────────────
    This is the key safety mechanism. We filter students by
    their CURRENT semester == from_semester. After a bulk promotion,
    those students are at from_semester+1. If the HOD accidentally
    runs bulk promote again with the same from_semester, the query
    returns ZERO students (none are at from_semester anymore).
    The system naturally prevents double promotion.

    SKIP CONDITIONS (student is included in query but skipped):
      - is_graduated = True    → already done, skip silently
      - semester >= max_sem    → already at ceiling, skip with warning

    Returns: dict with promoted/skipped/error counts + details
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return {'error': 'HOD profile not found.'}

    max_sem = 8 if program_type == 'UG' else 4

    # Validate: can't promote FROM the max semester
    if from_semester >= max_sem:
        return {
            'error': (
                f'Cannot promote from Semester {from_semester}. '
                f'{program_type} maximum is Semester {max_sem}.'
            )
        }

    if from_semester < 1:
        return {'error': 'Semester must be at least 1.'}

    # Fetch ALL students at this semester in this dept (active, not graduated)
    students = Student.query.filter_by(
        department_id=hod.department_id,
        semester=from_semester,
        program_type=program_type,
        is_graduated=False
    ).join(Student.user).filter(User.is_active == True).all()

    if not students:
        return {
            'promoted': 0, 'skipped': 0,
            'message': (
                f'No active {program_type} students found at '
                f'Semester {from_semester}. '
                f'They may have already been promoted.'   # ← explains double-promote
            )
        }

    promoted_list = []
    skipped_list  = []

    for student in students:
        # Safety: double-check graduation and ceiling
        if student.is_graduated:
            skipped_list.append(f'{student.full_name} (graduated)')
            continue
        if student.semester >= max_sem:
            skipped_list.append(f'{student.full_name} (at max sem)')
            continue

        old_sem          = student.semester
        student.semester += 1
        promoted_list.append(student)

        # Notify each student individually
        db.session.add(Notification(
            user_id=student.user_id, type='success',
            title='Semester Promotion',
            message=f'You have been promoted from Semester {old_sem} '
                    f'to Semester {student.semester} as part of '
                    f'a batch promotion.'
        ))

    db.session.commit()

    return {
        'promoted'      : len(promoted_list),
        'skipped'       : len(skipped_list),
        'to_semester'   : from_semester + 1,
        'promoted_names': [s.full_name for s in promoted_list],
        'skipped_names' : skipped_list,
        'message'       : (
            f'{len(promoted_list)} student(s) promoted to '
            f'Semester {from_semester + 1}. '
            f'{len(skipped_list)} skipped.'
        )
    }


# ══════════════════════════════════════════════════════════════════════
#  HOD DASHBOARD STATS
# ══════════════════════════════════════════════════════════════════════

def get_hod_dashboard_stats(hod_user):
    """
    Aggregate stats for the HOD dashboard summary cards.
    """
    hod = _get_hod_teacher(hod_user)
    if not hod:
        return {}

    dept_id = hod.department_id

    # Build semester-wise breakdown
    sem_breakdown = []
    max_ug = 8
    max_pg = 4

    for pt, max_s in [('UG', max_ug), ('PG', max_pg)]:
        for s in range(1, max_s + 1):
            count = Student.query.filter_by(
                department_id=dept_id,
                semester=s,
                program_type=pt,
                is_graduated=False
            ).join(Student.user).filter(User.is_active == True).count()
            if count > 0:
                sem_breakdown.append({
                    'label'       : f'{pt} Sem {s}',
                    'count'       : count,
                    'program_type': pt,
                    'semester'    : s,
                })

    return {
        'dept_name'       : hod.department.name,
        'dept_code'       : hod.department.code,
        'total_teachers'  : Teacher.query.filter_by(
                                department_id=dept_id,
                                is_hod=False,
                                is_active=True).count(),
        'total_subjects'  : Subject.query.filter_by(
                                department_id=dept_id,
                                is_active=True).count(),
        'active_students' : Student.query.filter_by(
                                department_id=dept_id,
                                is_graduated=False
                            ).join(Student.user).filter(User.is_active==True).count(),
        'graduated'       : Student.query.filter_by(
                                department_id=dept_id,
                                is_graduated=True).count(),
        'sem_breakdown'   : sem_breakdown,
    }