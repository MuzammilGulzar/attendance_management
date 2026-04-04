# """
# PRINCIPAL ROUTES
# ================
# Every route here is protected by @login_required + @principal_required.
# Routes are thin — they validate forms, call the service, show results.
# Business logic lives entirely in principal_service.py.
# """

# from flask import (Blueprint, render_template, redirect,
#                    url_for, flash, request, jsonify)
# from flask_login import login_required

# from app.decorators import principal_required
# from app.services.principal_service import (
#     create_department, update_department, deactivate_department,
#     get_all_departments, create_hod_account, assign_hod_to_dept,
#     deactivate_hod, get_all_hods, get_system_stats
# )
# from app.forms.principal_forms import (
#     CreateDepartmentForm, EditDepartmentForm,
#     CreateHODForm, AssignHODForm
# )

# principal_bp = Blueprint('principal', __name__)


# # ══════════════════════════════════════════════════════════════════════
# #  DASHBOARD
# # ══════════════════════════════════════════════════════════════════════

# @principal_bp.route('/dashboard')
# @login_required
# @principal_required
# def dashboard():
#     """
#     Principal's home — shows system-wide stats and
#     a per-department breakdown table.
#     """
#     stats = get_system_stats()
#     return render_template('principal/dashboard.html',
#                            title='Principal Dashboard', stats=stats)


# # ══════════════════════════════════════════════════════════════════════
# #  DEPARTMENT MANAGEMENT
# # ══════════════════════════════════════════════════════════════════════

# @principal_bp.route('/departments')
# @login_required
# @principal_required
# def list_departments():
#     """Show all active departments in a table."""
#     departments = get_all_departments()
#     return render_template('principal/departments.html',
#                            departments=departments,
#                            title='Manage Departments')


# @principal_bp.route('/departments/create', methods=['GET', 'POST'])
# @login_required
# @principal_required
# def create_department_view():
#     """
#     GET  → show the blank Create Department form
#     POST → validate, call service, redirect on success
#     """
#     form = CreateDepartmentForm()

#     if form.validate_on_submit():
#         dept, error = create_department(
#             name         = form.name.data,
#             code         = form.code.data,
#             program_type = form.program_type.data
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(
#                 f'Department "{dept.name}" ({dept.code}) created successfully!',
#                 'success'
#             )
#             return redirect(url_for('principal.list_departments'))

#     return render_template('principal/create_department.html',
#                            form=form, title='Create Department')


# @principal_bp.route('/departments/<int:dept_id>/edit', methods=['GET', 'POST'])
# @login_required
# @principal_required
# def edit_department(dept_id):
#     """Edit an existing department's name, code, or program type."""
#     from app.models import Department
#     dept = Department.query.get_or_404(dept_id)

#     form = EditDepartmentForm(obj=dept)   # pre-fills form with current values

#     if form.validate_on_submit():
#         updated, error = update_department(
#             dept_id      = dept_id,
#             name         = form.name.data,
#             code         = form.code.data,
#             program_type = form.program_type.data
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(f'Department "{updated.name}" updated successfully.', 'success')
#             return redirect(url_for('principal.list_departments'))

#     return render_template('principal/edit_department.html',
#                            form=form, dept=dept, title='Edit Department')


# @principal_bp.route('/departments/<int:dept_id>/deactivate', methods=['POST'])
# @login_required
# @principal_required
# def deactivate_department_view(dept_id):
#     """
#     Soft-delete a department. POST-only (no GET) because this is
#     a destructive action — we never trigger it from a link click.
#     """
#     success, error = deactivate_department(dept_id)
#     if error:
#         flash(error, 'danger')
#     else:
#         flash('Department deactivated. All records are preserved.', 'success')
#     return redirect(url_for('principal.list_departments'))


# # ══════════════════════════════════════════════════════════════════════
# #  HOD MANAGEMENT
# # ══════════════════════════════════════════════════════════════════════

# @principal_bp.route('/hods')
# @login_required
# @principal_required
# def list_hods():
#     """Show all active HODs and which department they manage."""
#     hods = get_all_hods()
#     return render_template('principal/hods.html',
#                            hods=hods, title='Manage HODs')


# @principal_bp.route('/hods/create', methods=['GET', 'POST'])
# @login_required
# @principal_required
# def create_hod():
#     """
#     Create a brand-new HOD account.
#     This creates both a User row AND a Teacher profile in one transaction.

#     Only the Principal can reach this — enforced by @principal_required.
#     An HOD cannot create another HOD.
#     """
#     form = CreateHODForm()

#     if form.validate_on_submit():
#         user, error = create_hod_account(
#             first_name    = form.first_name.data,
#             last_name     = form.last_name.data,
#             email         = form.email.data,
#             password      = form.password.data,
#             employee_id   = form.employee_id.data,
#             department_id = form.department_id.data
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(
#                 f'HOD account created for {user.full_name}. '
#                 f'They can now log in with their email.',
#                 'success'
#             )
#             return redirect(url_for('principal.list_hods'))

#     return render_template('principal/create_hod.html',
#                            form=form, title='Create HOD Account')


# @principal_bp.route('/hods/assign', methods=['GET', 'POST'])
# @login_required
# @principal_required
# def assign_hod():
#     """
#     Reassign the HOD role within a department.
#     Used when rotating HODs or replacing one who left.

#     The department dropdown is shown first. When the Principal
#     selects a department, an AJAX call fetches that dept's teachers
#     and populates the second dropdown.
#     """
#     form = AssignHODForm()

#     # AJAX endpoint — called by JS when department changes
#     if request.args.get('fetch_teachers'):
#         dept_id  = request.args.get('dept_id', type=int)
#         from app.models import Teacher
#         teachers = Teacher.query.filter_by(
#             department_id=dept_id,
#             is_active=True,
#             is_hod=False          # only non-HOD teachers shown
#         ).all()
#         return jsonify([
#             {'id': t.id, 'name': f'{t.full_name} ({t.employee_id})'}
#             for t in teachers
#         ])

#     if form.validate_on_submit():
#         # Populate teacher choices before validating
#         from app.models import Teacher
#         dept_id = form.department_id.data
#         teachers = Teacher.query.filter_by(department_id=dept_id,
#                                            is_active=True).all()
#         form.teacher_id.choices = [(t.id, t.full_name) for t in teachers]

#         if not form.validate():
#             flash('Please select a valid teacher.', 'danger')
#             return render_template('principal/assign_hod.html',
#                                    form=form, title='Assign HOD')

#         teacher, error = assign_hod_to_dept(
#             department_id = form.department_id.data,
#             teacher_id    = form.teacher_id.data
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(
#                 f'{teacher.full_name} has been assigned as HOD. '
#                 f'Their role has been updated.',
#                 'success'
#             )
#             return redirect(url_for('principal.list_hods'))

#     return render_template('principal/assign_hod.html',
#                            form=form, title='Assign HOD')


# @principal_bp.route('/hods/<int:teacher_id>/deactivate', methods=['POST'])
# @login_required
# @principal_required
# def deactivate_hod_view(teacher_id):
#     """Remove an HOD's access. POST-only for safety."""
#     success, error = deactivate_hod(teacher_id)
#     if error:
#         flash(error, 'danger')
#     else:
#         flash('HOD account deactivated. Their records are preserved.', 'success')
#     return redirect(url_for('principal.list_hods'))


##################------------updated-------------
"""
PRINCIPAL ROUTES
================
Every route here is protected by @login_required + @principal_required.
Routes are thin — they validate forms, call the service, show results.
Business logic lives entirely in principal_service.py.
"""

from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, jsonify)
from flask_login import login_required

from app.decorators import principal_required
from app.services.principal_service import (
    create_department, update_department, deactivate_department,
    get_all_departments, create_hod_account, assign_hod_to_dept,
    deactivate_hod, get_all_hods, get_system_stats
)
from app.forms.principal_forms import (
    CreateDepartmentForm, EditDepartmentForm,
    CreateHODForm, AssignHODForm
)

principal_bp = Blueprint('principal', __name__)


# ══════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════

@principal_bp.route('/dashboard')
@login_required
@principal_required
def dashboard():
    """
    Principal's home — shows system-wide stats and
    a per-department breakdown table.
    """
    stats = get_system_stats()
    return render_template('principal/dashboard.html',
                           title='Principal Dashboard', stats=stats)


# ══════════════════════════════════════════════════════════════════════
#  DEPARTMENT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

@principal_bp.route('/departments')
@login_required
@principal_required
def list_departments():
    """Show all active departments in a table."""
    departments = get_all_departments()
    return render_template('principal/departments.html',
                           departments=departments,
                           title='Manage Departments')


@principal_bp.route('/departments/create', methods=['GET', 'POST'])
@login_required
@principal_required
def create_department_view():
    """
    GET  → show the blank Create Department form
    POST → validate, call service, redirect on success
    """
    form = CreateDepartmentForm()

    if form.validate_on_submit():
        dept, error = create_department(
            name         = form.name.data,
            code         = form.code.data,
            program_type = form.program_type.data
        )
        if error:
            flash(error, 'danger')
        else:
            flash(
                f'Department "{dept.name}" ({dept.code}) created successfully!',
                'success'
            )
            return redirect(url_for('principal.list_departments'))

    return render_template('principal/create_department.html',
                           form=form, title='Create Department')


@principal_bp.route('/departments/<int:dept_id>/edit', methods=['GET', 'POST'])
@login_required
@principal_required
def edit_department(dept_id):
    """Edit an existing department's name, code, or program type."""
    from app.models.department import Department
    dept = Department.query.get_or_404(dept_id)

    form = EditDepartmentForm(obj=dept)   # pre-fills form with current values

    if form.validate_on_submit():
        updated, error = update_department(
            dept_id      = dept_id,
            name         = form.name.data,
            code         = form.code.data,
            program_type = form.program_type.data
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'Department "{updated.name}" updated successfully.', 'success')
            return redirect(url_for('principal.list_departments'))

    return render_template('principal/edit_department.html',
                           form=form, dept=dept, title='Edit Department')


@principal_bp.route('/departments/<int:dept_id>/deactivate', methods=['POST'])
@login_required
@principal_required
def deactivate_department_view(dept_id):
    """
    Soft-delete a department. POST-only (no GET) because this is
    a destructive action — we never trigger it from a link click.
    """
    success, error = deactivate_department(dept_id)
    if error:
        flash(error, 'danger')
    else:
        flash('Department deactivated. All records are preserved.', 'success')
    return redirect(url_for('principal.list_departments'))


# ══════════════════════════════════════════════════════════════════════
#  HOD MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

@principal_bp.route('/hods')
@login_required
@principal_required
def list_hods():
    """Show all active HODs and which department they manage."""
    hods = get_all_hods()
    return render_template('principal/hods.html',
                           hods=hods, title='Manage HODs')


@principal_bp.route('/hods/create', methods=['GET', 'POST'])
@login_required
@principal_required
def create_hod():
    """
    Create a brand-new HOD account.
    This creates both a User row AND a Teacher profile in one transaction.

    Only the Principal can reach this — enforced by @principal_required.
    An HOD cannot create another HOD.
    """
    form = CreateHODForm()

    if form.validate_on_submit():
        user, error = create_hod_account(
            first_name    = form.first_name.data,
            last_name     = form.last_name.data,
            email         = form.email.data,
            password      = form.password.data,
            employee_id   = form.employee_id.data,
            department_id = form.department_id.data
        )
        if error:
            flash(error, 'danger')
        else:
            flash(
                f'HOD account created for {user.full_name}. '
                f'They can now log in with their email.',
                'success'
            )
            return redirect(url_for('principal.list_hods'))

    return render_template('principal/create_hod.html',
                           form=form, title='Create HOD Account')


@principal_bp.route('/hods/assign', methods=['GET', 'POST'])
@login_required
@principal_required
def assign_hod():
    """
    Reassign the HOD role within a department.
    Used when rotating HODs or replacing one who left.

    The department dropdown is shown first. When the Principal
    selects a department, an AJAX call fetches that dept's teachers
    and populates the second dropdown.
    """
    form = AssignHODForm()

    # AJAX endpoint — called by JS when department changes
    if request.args.get('fetch_teachers'):
        dept_id  = request.args.get('dept_id', type=int)
        from app.models import Teacher
        teachers = Teacher.query.filter_by(
            department_id=dept_id,
            is_active=True,
            is_hod=False          # only non-HOD teachers shown
        ).all()
        return jsonify([
            {'id': t.id, 'name': f'{t.full_name} ({t.employee_id})'}
            for t in teachers
        ])

    if form.validate_on_submit():
        # Populate teacher choices before validating
        from app.models import Teacher
        dept_id = form.department_id.data
        teachers = Teacher.query.filter_by(department_id=dept_id,
                                           is_active=True).all()
        form.teacher_id.choices = [(t.id, t.full_name) for t in teachers]

        if not form.validate():
            flash('Please select a valid teacher.', 'danger')
            return render_template('principal/assign_hod.html',
                                   form=form, title='Assign HOD')

        teacher, error = assign_hod_to_dept(
            department_id = form.department_id.data,
            teacher_id    = form.teacher_id.data
        )
        if error:
            flash(error, 'danger')
        else:
            flash(
                f'{teacher.full_name} has been assigned as HOD. '
                f'Their role has been updated.',
                'success'
            )
            return redirect(url_for('principal.list_hods'))

    return render_template('principal/assign_hod.html',
                           form=form, title='Assign HOD')


@principal_bp.route('/hods/<int:teacher_id>/deactivate', methods=['POST'])
@login_required
@principal_required
def deactivate_hod_view(teacher_id):
    """Remove an HOD's access. POST-only for safety."""
    success, error = deactivate_hod(teacher_id)
    if error:
        flash(error, 'danger')
    else:
        flash('HOD account deactivated. Their records are preserved.', 'success')
    return redirect(url_for('principal.list_hods'))