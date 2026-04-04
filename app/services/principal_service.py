"""
PRINCIPAL SERVICE
=================
All business logic for Principal actions lives here.
Routes call these functions — they never touch the DB directly.

Functions:
  create_department()       → add a new department
  create_hod_account()      → create User + Teacher profile for a new HOD
  assign_hod_to_dept()      → move HOD role from one teacher to another
  deactivate_department()   → soft-delete a department
  get_system_stats()        → counts for dashboard
"""

from app import db
from app.models.user       import User, Role
from app.models.department import Department
from app.models.teacher    import Teacher
from app.models.notification import Notification


# ── DEPARTMENTS ──────────────────────────────────────────────────────

def create_department(name: str, code: str, program_type: str):
    """
    Create a new department.

    Validates:
      - name and code must be unique
      - program_type must be 'UG', 'PG', or 'both'

    Returns: (department, None)  on success
             (None, error_msg)   on failure
    """
    name = name.strip()
    code = code.strip().upper()

    if not name or not code:
        return None, 'Department name and code are required.'

    if program_type not in ('UG', 'PG', 'both'):
        return None, "Program type must be 'UG', 'PG', or 'both'."

    # Check uniqueness
    if Department.query.filter_by(name=name).first():
        return None, f'A department named "{name}" already exists.'

    if Department.query.filter_by(code=code).first():
        return None, f'Department code "{code}" is already taken.'

    dept = Department(name=name, code=code, program_type=program_type)
    db.session.add(dept)
    db.session.commit()
    return dept, None


def update_department(dept_id: int, name: str, code: str, program_type: str):
    """
    Update an existing department's details.

    Returns: (department, None)  on success
             (None, error_msg)   on failure
    """
    dept = Department.query.get(dept_id)
    if not dept:
        return None, 'Department not found.'

    name = name.strip()
    code = code.strip().upper()

    # Check uniqueness — exclude the current dept from the check
    existing_name = Department.query.filter(
        Department.name == name, Department.id != dept_id
    ).first()
    if existing_name:
        return None, f'A department named "{name}" already exists.'

    existing_code = Department.query.filter(
        Department.code == code, Department.id != dept_id
    ).first()
    if existing_code:
        return None, f'Department code "{code}" is already taken.'

    if program_type not in ('UG', 'PG', 'both'):
        return None, "Program type must be 'UG', 'PG', or 'both'."

    dept.name         = name
    dept.code         = code
    dept.program_type = program_type
    db.session.commit()
    return dept, None


def deactivate_department(dept_id: int):
    """
    Soft-delete a department (sets is_active=False).
    We never hard-delete — students and records must remain.

    Returns: (True, None) or (False, error_msg)
    """
    dept = Department.query.get(dept_id)
    if not dept:
        return False, 'Department not found.'

    # Safety check: do not deactivate if students are still active
    from app.models.student import Student
    active_students = Student.query.filter_by(
        department_id=dept_id, is_graduated=False
    ).count()

    if active_students > 0:
        return False, (
            f'Cannot deactivate "{dept.name}": '
            f'{active_students} active student(s) still enrolled. '
            f'Graduate or transfer them first.'
        )

    dept.is_active = False
    db.session.commit()
    return True, None


def get_all_departments(include_inactive=False):
    """Fetch all departments, optionally including deactivated ones."""
    query = Department.query
    if not include_inactive:
        query = query.filter_by(is_active=True)
    return query.order_by(Department.name).all()


# ── HOD MANAGEMENT ────────────────────────────────────────────────────

def create_hod_account(first_name: str, last_name: str, email: str,
                        password: str, employee_id: str, department_id: int):
    """
    Create a full HOD account. This is a two-step operation:
      Step 1: Create the User row (login credentials + role='hod')
      Step 2: Create the Teacher row (department + employee_id + is_hod=True)

    If the department already has an HOD, we do NOT remove them.
    The Principal must explicitly reassign using assign_hod_to_dept().

    Returns: (user, None)       on success
             (None, error_msg)  on failure
    """
    # ── Validate inputs ──
    email       = email.strip().lower()
    employee_id = employee_id.strip().upper()

    if not all([first_name, last_name, email, password, employee_id]):
        return None, 'All fields are required.'

    if len(password) < 8:
        return None, 'Password must be at least 8 characters.'

    # ── Check uniqueness ──
    if User.query.filter_by(email=email).first():
        return None, f'Email "{email}" is already registered.'

    if Teacher.query.filter_by(employee_id=employee_id).first():
        return None, f'Employee ID "{employee_id}" is already in use.'

    dept = Department.query.get(department_id)
    if not dept:
        return None, 'Selected department does not exist.'

    if not dept.is_active:
        return None, f'Department "{dept.name}" is inactive.'

    # ── Create User ──
    user = User(
        email      = email,
        first_name = first_name.strip(),
        last_name  = last_name.strip(),
        role       = Role.HOD,
        is_active  = True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()   # get user.id without committing yet

    # ── Create Teacher profile ──
    teacher = Teacher(
        user_id       = user.id,
        department_id = department_id,
        employee_id   = employee_id,
        is_hod        = True
    )
    db.session.add(teacher)
    db.session.commit()

    # ── Notify the new HOD ──
    notif = Notification(
        user_id = user.id,
        type    = 'success',
        title   = 'Welcome as HOD',
        message = (
            f'You have been appointed as Head of Department for '
            f'{dept.name}. You can now manage your department, '
            f'promote students, and oversee attendance.'
        )
    )
    db.session.add(notif)
    db.session.commit()

    return user, None


def assign_hod_to_dept(department_id: int, teacher_id: int):
    """
    Make an existing teacher the HOD of a department.

    Steps:
      1. Find the current HOD of this dept and remove their HOD flag
      2. Give the HOD flag to the selected teacher
      3. Update the old HOD's User.role to 'teacher'
      4. Update the new HOD's User.role to 'hod'

    This is used when rotating HODs or replacing one who left.

    Returns: (teacher, None) or (None, error_msg)
    """
    dept = Department.query.get(department_id)
    if not dept:
        return None, 'Department not found.'

    new_hod = Teacher.query.get(teacher_id)
    if not new_hod:
        return None, 'Teacher not found.'

    if new_hod.department_id != department_id:
        return None, 'That teacher does not belong to this department.'

    # ── Step 1: Remove current HOD flag ──
    current_hod = Teacher.query.filter_by(
        department_id=department_id, is_hod=True
    ).first()

    if current_hod and current_hod.id != new_hod.id:
        current_hod.is_hod        = False
        current_hod.user.role     = Role.TEACHER   # downgrade role

    # ── Step 2: Promote new teacher to HOD ──
    new_hod.is_hod    = True
    new_hod.user.role = Role.HOD                   # upgrade role

    db.session.commit()

    # ── Notify the new HOD ──
    notif = Notification(
        user_id = new_hod.user_id,
        type    = 'success',
        title   = 'HOD Assignment',
        message = f'You have been assigned as HOD of {dept.name}.'
    )
    db.session.add(notif)
    db.session.commit()

    return new_hod, None


def deactivate_hod(teacher_id: int):
    """
    Remove an HOD's access without deleting their data.
    Sets User.is_active=False and removes the is_hod flag.

    The department will show as "HOD not assigned" until a new one is set.

    Returns: (True, None) or (False, error_msg)
    """
    teacher = Teacher.query.get(teacher_id)
    if not teacher or not teacher.is_hod:
        return False, 'HOD not found.'

    teacher.is_hod        = False
    teacher.is_active     = False
    teacher.user.is_active = False
    db.session.commit()
    return True, None


def get_all_hods():
    """Return all active HOD teacher profiles with their user and dept data."""
    return (
        Teacher.query
        .filter_by(is_hod=True, is_active=True)
        .join(Teacher.user)
        .join(Teacher.department)
        .order_by(Department.name)
        .all()
    )


# ── SYSTEM STATS ──────────────────────────────────────────────────────

def get_system_stats():
    """
    Aggregate numbers for the Principal dashboard.
    Returns a plain dict — easy to pass to a template.
    """
    from app.models.student import Student

    depts = Department.query.filter_by(is_active=True).all()

    dept_breakdown = []
    for dept in depts:
        dept_breakdown.append({
            'name'             : dept.name,
            'code'             : dept.code,
            'program_type'     : dept.program_type,
            'hod_name'         : dept.hod.full_name if dept.hod else 'Not assigned',
            'active_students'  : Student.query.filter_by(
                                    department_id=dept.id,
                                    is_graduated=False).count(),
            'graduated_students': Student.query.filter_by(
                                    department_id=dept.id,
                                    is_graduated=True).count(),
            'teachers'         : Teacher.query.filter_by(
                                    department_id=dept.id,
                                    is_hod=False,
                                    is_active=True).count(),
        })

    return {
        'total_departments'  : len(depts),
        'total_hods'         : Teacher.query.filter_by(is_hod=True,  is_active=True).count(),
        'total_teachers'     : Teacher.query.filter_by(is_hod=False, is_active=True).count(),
        'total_students'     : Student.query.filter_by(is_graduated=False).count(),
        'graduated_students' : Student.query.filter_by(is_graduated=True).count(),
        'dept_breakdown'     : dept_breakdown,
    }