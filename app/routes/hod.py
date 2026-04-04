# """
# HOD ROUTES
# ==========
# All HOD dashboard routes. Thin controllers — logic in hod_service.py.
# Every route uses @login_required + @hod_required minimum.
# """

# from flask import (Blueprint, render_template, redirect,
#                    url_for, flash, request, g)
# from flask_login import login_required, current_user

# from app.decorators import (hod_required, hod_owns_student,
#                              hod_owns_attendance, graduation_not_locked,
#                              can_graduate_check)
# # graduation_service imported inline in graduation routes to avoid circular imports
# from app.services.hod_service import (
#     # teacher
#     create_teacher, update_teacher, deactivate_teacher,
#     get_dept_teachers, assign_subject_to_teacher,
#     unassign_subject_from_teacher,
#     # subject
#     create_subject, update_subject, deactivate_subject, get_dept_subjects,
#     # student
#     create_student, soft_delete_student, get_students_by_semester,
#     # promotion
#     promote_single_student, bulk_promote,
#     # stats
#     get_hod_dashboard_stats,
# )
# from app.forms.hod_forms import (
#     CreateTeacherForm, EditTeacherForm, AssignSubjectForm,
#     CreateSubjectForm, EditSubjectForm,
#     CreateStudentForm, DeleteStudentForm, BulkPromoteForm,
# )

# hod_bp = Blueprint('hod', __name__)


# # ══════════════════════════════════════════════════════════════════════
# #  DASHBOARD
# # ══════════════════════════════════════════════════════════════════════

# @hod_bp.route('/dashboard')
# @login_required
# @hod_required
# def dashboard():
#     stats = get_hod_dashboard_stats(current_user)
#     return render_template('hod/dashboard.html',
#                            title='HOD Dashboard', stats=stats)


# # ══════════════════════════════════════════════════════════════════════
# #  TEACHER MANAGEMENT
# # ══════════════════════════════════════════════════════════════════════

# @hod_bp.route('/teachers')
# @login_required
# @hod_required
# def list_teachers():
#     teachers = get_dept_teachers(current_user)
#     return render_template('hod/teachers.html',
#                            teachers=teachers, title='My Teachers')


# @hod_bp.route('/teachers/create', methods=['GET', 'POST'])
# @login_required
# @hod_required
# def create_teacher_view():
#     form = CreateTeacherForm()
#     if form.validate_on_submit():
#         user, error = create_teacher(
#             hod_user    = current_user,
#             first_name  = form.first_name.data,
#             last_name   = form.last_name.data,
#             email       = form.email.data,
#             password    = form.password.data,
#             employee_id = form.employee_id.data,
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(f'Teacher {user.full_name} created successfully.', 'success')
#             return redirect(url_for('hod.list_teachers'))
#     return render_template('hod/create_teacher.html',
#                            form=form, title='Add Teacher')


# @hod_bp.route('/teachers/<int:teacher_id>/edit', methods=['GET', 'POST'])
# @login_required
# @hod_required
# def edit_teacher(teacher_id):
#     from app.models import Teacher
#     teacher = Teacher.query.get_or_404(teacher_id)
#     form = EditTeacherForm(obj=teacher.user)
#     if request.method == 'GET':
#         form.employee_id.data = teacher.employee_id

#     if form.validate_on_submit():
#         updated, error = update_teacher(
#             hod_user    = current_user,
#             teacher_id  = teacher_id,
#             first_name  = form.first_name.data,
#             last_name   = form.last_name.data,
#             employee_id = form.employee_id.data,
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(f'{updated.full_name} updated.', 'success')
#             return redirect(url_for('hod.list_teachers'))
#     return render_template('hod/edit_teacher.html',
#                            form=form, teacher=teacher, title='Edit Teacher')


# @hod_bp.route('/teachers/<int:teacher_id>/deactivate', methods=['POST'])
# @login_required
# @hod_required
# def deactivate_teacher_view(teacher_id):
#     success, error = deactivate_teacher(current_user, teacher_id)
#     if error:
#         flash(error, 'danger')
#     else:
#         flash('Teacher deactivated. Their records are preserved.', 'success')
#     return redirect(url_for('hod.list_teachers'))


# @hod_bp.route('/teachers/assign-subject', methods=['GET', 'POST'])
# @login_required
# @hod_required
# def assign_subject():
#     hod_teacher = current_user.teacher_profile
#     dept_id = hod_teacher.department_id if hod_teacher else None
#     form = AssignSubjectForm(dept_id=dept_id)

#     if form.validate_on_submit():
#         success, error = assign_subject_to_teacher(
#             current_user, form.teacher_id.data, form.subject_id.data
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash('Subject assigned successfully.', 'success')
#             return redirect(url_for('hod.list_teachers'))
#     return render_template('hod/assign_subject.html',
#                            form=form, title='Assign Subject to Teacher')


# @hod_bp.route('/teachers/<int:teacher_id>/unassign/<int:subject_id>',
#               methods=['POST'])
# @login_required
# @hod_required
# def unassign_subject(teacher_id, subject_id):
#     success, error = unassign_subject_from_teacher(
#         current_user, teacher_id, subject_id
#     )
#     if error:
#         flash(error, 'danger')
#     else:
#         flash('Subject unassigned.', 'success')
#     return redirect(url_for('hod.list_teachers'))


# # ══════════════════════════════════════════════════════════════════════
# #  SUBJECT MANAGEMENT
# # ══════════════════════════════════════════════════════════════════════

# @hod_bp.route('/subjects')
# @login_required
# @hod_required
# def list_subjects():
#     subjects = get_dept_subjects(current_user)
#     return render_template('hod/subjects.html',
#                            subjects=subjects, title='My Subjects')


# @hod_bp.route('/subjects/create', methods=['GET', 'POST'])
# @login_required
# @hod_required
# def create_subject_view():
#     form = CreateSubjectForm()
#     if form.validate_on_submit():
#         subject, error = create_subject(
#             hod_user      = current_user,
#             name          = form.name.data,
#             code          = form.code.data,
#             semester      = form.semester.data,
#             program_type  = form.program_type.data,
#             total_classes = form.total_classes.data,
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(f'Subject "{subject.name}" created.', 'success')
#             return redirect(url_for('hod.list_subjects'))
#     return render_template('hod/create_subject.html',
#                            form=form, title='Create Subject')


# @hod_bp.route('/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
# @login_required
# @hod_required
# def edit_subject(subject_id):
#     from app.models import Subject
#     subject = Subject.query.get_or_404(subject_id)
#     form = EditSubjectForm(obj=subject)
#     if form.validate_on_submit():
#         updated, error = update_subject(
#             hod_user      = current_user,
#             subject_id    = subject_id,
#             name          = form.name.data,
#             code          = form.code.data,
#             semester      = form.semester.data,
#             program_type  = form.program_type.data,
#             total_classes = form.total_classes.data,
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(f'Subject "{updated.name}" updated.', 'success')
#             return redirect(url_for('hod.list_subjects'))
#     return render_template('hod/edit_subject.html',
#                            form=form, subject=subject, title='Edit Subject')


# @hod_bp.route('/subjects/<int:subject_id>/deactivate', methods=['POST'])
# @login_required
# @hod_required
# def deactivate_subject_view(subject_id):
#     success, error = deactivate_subject(current_user, subject_id)
#     if error:
#         flash(error, 'danger')
#     else:
#         flash('Subject deactivated. Attendance records preserved.', 'success')
#     return redirect(url_for('hod.list_subjects'))


# # ══════════════════════════════════════════════════════════════════════
# #  STUDENT MANAGEMENT
# # ══════════════════════════════════════════════════════════════════════

# @hod_bp.route('/students')
# @login_required
# @hod_required
# def list_students():
#     """
#     Show students filtered by semester and program_type.
#     Query params: ?semester=3&program_type=UG
#     Default: show all active students grouped by semester.
#     """
#     semester     = request.args.get('semester', type=int)
#     program_type = request.args.get('program_type')
#     students     = get_students_by_semester(
#         current_user, semester=semester, program_type=program_type
#     )
#     stats = get_hod_dashboard_stats(current_user)
#     return render_template('hod/students.html',
#                            students=students,
#                            sem_breakdown=stats.get('sem_breakdown', []),
#                            selected_sem=semester,
#                            selected_pt=program_type,
#                            title='My Students')


# @hod_bp.route('/students/create', methods=['GET', 'POST'])
# @login_required
# @hod_required
# def create_student_view():
#     form = CreateStudentForm()
#     if form.validate_on_submit():
#         user, error = create_student(
#             hod_user       = current_user,
#             first_name     = form.first_name.data,
#             last_name      = form.last_name.data,
#             email          = form.email.data,
#             password       = form.password.data,
#             roll_number    = form.roll_number.data,
#             admission_year = form.admission_year.data,
#             program_type   = form.program_type.data,
#             semester       = form.semester.data,
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(f'Student {user.full_name} enrolled successfully.', 'success')
#             return redirect(url_for('hod.list_students'))
#     return render_template('hod/create_student.html',
#                            form=form, title='Enroll Student')


# @hod_bp.route('/students/<int:student_id>/delete', methods=['GET', 'POST'])
# @login_required
# @hod_required
# @hod_owns_student
# def delete_student(student_id):
#     """
#     Soft-delete a student WITH a mandatory reason.
#     @hod_owns_student pre-fetches and verifies department ownership.
#     """
#     student = g.owned_student
#     form    = DeleteStudentForm()

#     if form.validate_on_submit():
#         success, error = soft_delete_student(
#             current_user, student_id, form.reason.data
#         )
#         if error:
#             flash(error, 'danger')
#         else:
#             flash(
#                 f'{student.full_name} has been removed. '
#                 f'Their academic records are preserved.',
#                 'success'
#             )
#             return redirect(url_for('hod.list_students'))

#     return render_template('hod/delete_student.html',
#                            form=form, student=student,
#                            title='Remove Student')


# # ══════════════════════════════════════════════════════════════════════
# #  SEMESTER PROMOTION
# # ══════════════════════════════════════════════════════════════════════

# @hod_bp.route('/students/<int:student_id>/promote', methods=['POST'])
# @login_required
# @hod_required
# @hod_owns_student
# @graduation_not_locked
# def promote_student(student_id):
#     """Promote a single student one semester forward."""
#     student, error = promote_single_student(current_user, student_id)
#     if error:
#         flash(error, 'warning')
#     else:
#         flash(
#             f'{student.full_name} promoted to Semester {student.semester}.',
#             'success'
#         )
#     return redirect(url_for('hod.list_students'))


# @hod_bp.route('/students/bulk-promote', methods=['GET', 'POST'])
# @login_required
# @hod_required
# def bulk_promote_view():
#     """
#     Bulk promotion form.
#     HOD picks: program_type + from_semester → all eligible students promoted.
#     """
#     form = BulkPromoteForm()
#     result = None

#     if form.validate_on_submit():
#         result = bulk_promote(
#             hod_user      = current_user,
#             from_semester = form.from_semester.data,
#             program_type  = form.program_type.data,
#         )
#         if 'error' in result:
#             flash(result['error'], 'danger')
#             result = None
#         else:
#             flash(result['message'],
#                   'success' if result['promoted'] > 0 else 'info')

#     return render_template('hod/bulk_promote.html',
#                            form=form, result=result,
#                            title='Bulk Semester Promotion')


# # ══════════════════════════════════════════════════════════════════════
# #  GRADUATION (kept from Step 5, uses decorators from Step 5)
# # ══════════════════════════════════════════════════════════════════════

# @hod_bp.route('/students/<int:student_id>/graduate', methods=['GET', 'POST'])
# @login_required
# @hod_required
# @hod_owns_student
# def graduate_student(student_id):
#     """
#     Graduate a single student.
#     GET  → show confirmation form with student details
#     POST → validate form, call graduation_service, redirect

#     Note: decorators @graduation_not_locked and @can_graduate_check
#     from Step 5 have been REMOVED here because the graduation_service
#     now handles all those validations internally — single source of truth.
#     The service returns a clear error message if any rule is violated.
#     """
#     from app.services.graduation_service import graduate_student as svc_graduate
#     from app.forms.graduation_forms import GraduateStudentForm

#     student = g.owned_student
#     form    = GraduateStudentForm()

#     if form.validate_on_submit():
#         graduated, error = svc_graduate(
#             hod_user   = current_user,
#             student_id = student_id,
#             reason     = form.reason.data
#         )
#         if error:
#             flash(error, 'danger')
#             return render_template('hod/graduation/confirm.html',
#                                    form=form, student=student,
#                                    title='Confirm Graduation')
#         flash(
#             f'{graduated.full_name} has been graduated successfully '
#             f'from {graduated.program_type} Semester {graduated.graduation_semester}. '
#             f'Their login has been disabled.',
#             'success'
#         )
#         return redirect(url_for('hod.graduation_management'))

#     return render_template('hod/graduation/confirm.html',
#                            form=form, student=student,
#                            title='Confirm Graduation')


# @hod_bp.route('/graduation')
# @login_required
# @hod_required
# def graduation_management():
#     """
#     Central graduation management page.
#     Shows: eligible students, graduated alumni, stats, bulk graduate option.
#     """
#     from app.services.graduation_service import (
#         get_graduation_eligible_students,
#         get_graduated_students,
#         get_graduation_stats
#     )
#     eligible   = get_graduation_eligible_students(current_user)
#     alumni     = get_graduated_students(current_user)
#     stats      = get_graduation_stats(current_user)
#     return render_template('hod/graduation/management.html',
#                            eligible=eligible,
#                            alumni=alumni,
#                            stats=stats,
#                            title='Graduation Management')


# @hod_bp.route('/graduation/alumni')
# @login_required
# @hod_required
# def alumni_list():
#     """View all graduated students with filters."""
#     from app.services.graduation_service import get_graduated_students
#     program_type = request.args.get('program_type')
#     year         = request.args.get('year')
#     alumni       = get_graduated_students(current_user,
#                                           program_type=program_type,
#                                           year=year)
#     return render_template('hod/graduation/alumni.html',
#                            alumni=alumni,
#                            selected_pt=program_type,
#                            selected_year=year,
#                            title='Alumni Records')


# @hod_bp.route('/graduation/bulk', methods=['GET', 'POST'])
# @login_required
# @hod_required
# def bulk_graduate_view():
#     """Graduate an entire batch at once."""
#     from app.services.graduation_service import bulk_graduate
#     from app.forms.graduation_forms import BulkGraduateForm
#     form   = BulkGraduateForm()
#     result = None

#     if form.validate_on_submit():
#         result = bulk_graduate(
#             hod_user     = current_user,
#             program_type = form.program_type.data,
#             semester     = form.semester.data,
#             reason       = form.reason.data,
#         )
#         if 'error' in result:
#             flash(result['error'], 'danger')
#             result = None
#         else:
#             flash(result['message'],
#                   'success' if result['graduated'] > 0 else 'info')

#     return render_template('hod/graduation/bulk.html',
#                            form=form, result=result,
#                            title='Bulk Graduation')


# # ══════════════════════════════════════════════════════════════════════
# #  ATTENDANCE EDITING (from Step 5)
# # ══════════════════════════════════════════════════════════════════════

# @hod_bp.route('/attendance/<int:attendance_id>/edit', methods=['GET', 'POST'])
# @login_required
# @hod_required
# @hod_owns_attendance
# def edit_attendance(attendance_id):
#     from app import db
#     record = g.owned_attendance

#     if request.method == 'POST':
#         new_status = request.form.get('status')
#         reason     = request.form.get('reason', '').strip()

#         if not reason:
#             flash('A reason is required for editing attendance.', 'danger')
#         elif new_status not in ('present', 'absent', 'late', 'excused'):
#             flash('Invalid status.', 'danger')
#         else:
#             record.apply_hod_edit(new_status, reason, current_user.teacher_profile)
#             db.session.commit()
#             flash('Attendance record updated.', 'success')
#             return redirect(url_for('hod.dashboard'))

#     return render_template('hod/edit_attendance.html',
#                            record=record, title='Edit Attendance')

######-------------updated--------
"""
HOD ROUTES
==========
All HOD dashboard routes. Thin controllers — logic in hod_service.py.
Every route uses @login_required + @hod_required minimum.
"""

from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, g)
from flask_login import login_required, current_user

from app.decorators import (hod_required, hod_owns_student,
                             hod_owns_attendance, graduation_not_locked,
                             can_graduate_check)
# graduation_service imported inline in graduation routes to avoid circular imports
from app.services.hod_service import (
    # teacher
    create_teacher, update_teacher, deactivate_teacher,
    get_dept_teachers, assign_subject_to_teacher,
    unassign_subject_from_teacher,
    # subject
    create_subject, update_subject, deactivate_subject, get_dept_subjects,
    # student
    create_student, soft_delete_student, get_students_by_semester,
    # promotion
    promote_single_student, bulk_promote,
    # stats
    get_hod_dashboard_stats,
)
from app.forms.hod_forms import (
    CreateTeacherForm, EditTeacherForm, AssignSubjectForm,
    CreateSubjectForm, EditSubjectForm,
    CreateStudentForm, DeleteStudentForm, BulkPromoteForm,
)

hod_bp = Blueprint('hod', __name__)


# ══════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/dashboard')
@login_required
@hod_required
def dashboard():
    stats = get_hod_dashboard_stats(current_user)
    return render_template('hod/dashboard.html',
                           title='HOD Dashboard', stats=stats)


# ══════════════════════════════════════════════════════════════════════
#  TEACHER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/teachers')
@login_required
@hod_required
def list_teachers():
    teachers = get_dept_teachers(current_user)
    return render_template('hod/teachers.html',
                           teachers=teachers, title='My Teachers')


@hod_bp.route('/teachers/create', methods=['GET', 'POST'])
@login_required
@hod_required
def create_teacher_view():
    form = CreateTeacherForm()
    if form.validate_on_submit():
        user, error = create_teacher(
            hod_user    = current_user,
            first_name  = form.first_name.data,
            last_name   = form.last_name.data,
            email       = form.email.data,
            password    = form.password.data,
            employee_id = form.employee_id.data,
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'Teacher {user.full_name} created successfully.', 'success')
            return redirect(url_for('hod.list_teachers'))
    return render_template('hod/create_teacher.html',
                           form=form, title='Add Teacher')


@hod_bp.route('/teachers/<int:teacher_id>/edit', methods=['GET', 'POST'])
@login_required
@hod_required
def edit_teacher(teacher_id):
    from app.models.teacher import Teacher
    teacher = Teacher.query.get_or_404(teacher_id)
    form = EditTeacherForm(obj=teacher.user)
    if request.method == 'GET':
        form.employee_id.data = teacher.employee_id

    if form.validate_on_submit():
        updated, error = update_teacher(
            hod_user    = current_user,
            teacher_id  = teacher_id,
            first_name  = form.first_name.data,
            last_name   = form.last_name.data,
            employee_id = form.employee_id.data,
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'{updated.full_name} updated.', 'success')
            return redirect(url_for('hod.list_teachers'))
    return render_template('hod/edit_teacher.html',
                           form=form, teacher=teacher, title='Edit Teacher')


@hod_bp.route('/teachers/<int:teacher_id>/deactivate', methods=['POST'])
@login_required
@hod_required
def deactivate_teacher_view(teacher_id):
    success, error = deactivate_teacher(current_user, teacher_id)
    if error:
        flash(error, 'danger')
    else:
        flash('Teacher deactivated. Their records are preserved.', 'success')
    return redirect(url_for('hod.list_teachers'))


@hod_bp.route('/teachers/assign-subject', methods=['GET', 'POST'])
@login_required
@hod_required
def assign_subject():
    hod_teacher = current_user.teacher_profile
    dept_id = hod_teacher.department_id if hod_teacher else None
    form = AssignSubjectForm(dept_id=dept_id)

    if form.validate_on_submit():
        success, error = assign_subject_to_teacher(
            current_user, form.teacher_id.data, form.subject_id.data
        )
        if error:
            flash(error, 'danger')
        else:
            flash('Subject assigned successfully.', 'success')
            return redirect(url_for('hod.list_teachers'))
    return render_template('hod/assign_subject.html',
                           form=form, title='Assign Subject to Teacher')


@hod_bp.route('/teachers/<int:teacher_id>/unassign/<int:subject_id>',
              methods=['POST'])
@login_required
@hod_required
def unassign_subject(teacher_id, subject_id):
    success, error = unassign_subject_from_teacher(
        current_user, teacher_id, subject_id
    )
    if error:
        flash(error, 'danger')
    else:
        flash('Subject unassigned.', 'success')
    return redirect(url_for('hod.list_teachers'))


# ══════════════════════════════════════════════════════════════════════
#  SUBJECT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/subjects')
@login_required
@hod_required
def list_subjects():
    subjects = get_dept_subjects(current_user)
    return render_template('hod/subjects.html',
                           subjects=subjects, title='My Subjects')


@hod_bp.route('/subjects/create', methods=['GET', 'POST'])
@login_required
@hod_required
def create_subject_view():
    form = CreateSubjectForm()
    if form.validate_on_submit():
        subject, error = create_subject(
            hod_user      = current_user,
            name          = form.name.data,
            code          = form.code.data,
            semester      = form.semester.data,
            program_type  = form.program_type.data,
            total_classes = form.total_classes.data,
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'Subject "{subject.name}" created.', 'success')
            return redirect(url_for('hod.list_subjects'))
    return render_template('hod/create_subject.html',
                           form=form, title='Create Subject')


@hod_bp.route('/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
@hod_required
def edit_subject(subject_id):
    from app.models.subject import Subject
    subject = Subject.query.get_or_404(subject_id)
    form = EditSubjectForm(obj=subject)
    if form.validate_on_submit():
        updated, error = update_subject(
            hod_user      = current_user,
            subject_id    = subject_id,
            name          = form.name.data,
            code          = form.code.data,
            semester      = form.semester.data,
            program_type  = form.program_type.data,
            total_classes = form.total_classes.data,
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'Subject "{updated.name}" updated.', 'success')
            return redirect(url_for('hod.list_subjects'))
    return render_template('hod/edit_subject.html',
                           form=form, subject=subject, title='Edit Subject')


@hod_bp.route('/subjects/<int:subject_id>/deactivate', methods=['POST'])
@login_required
@hod_required
def deactivate_subject_view(subject_id):
    success, error = deactivate_subject(current_user, subject_id)
    if error:
        flash(error, 'danger')
    else:
        flash('Subject deactivated. Attendance records preserved.', 'success')
    return redirect(url_for('hod.list_subjects'))


# ══════════════════════════════════════════════════════════════════════
#  STUDENT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/students')
@login_required
@hod_required
def list_students():
    """
    Show students filtered by semester and program_type.
    Query params: ?semester=3&program_type=UG
    Default: show all active students grouped by semester.
    """
    semester     = request.args.get('semester', type=int)
    program_type = request.args.get('program_type')
    students     = get_students_by_semester(
        current_user, semester=semester, program_type=program_type
    )
    stats = get_hod_dashboard_stats(current_user)
    return render_template('hod/students.html',
                           students=students,
                           sem_breakdown=stats.get('sem_breakdown', []),
                           selected_sem=semester,
                           selected_pt=program_type,
                           title='My Students')


@hod_bp.route('/students/create', methods=['GET', 'POST'])
@login_required
@hod_required
def create_student_view():
    form = CreateStudentForm()
    if form.validate_on_submit():
        user, error = create_student(
            hod_user       = current_user,
            first_name     = form.first_name.data,
            last_name      = form.last_name.data,
            email          = form.email.data,
            password       = form.password.data,
            roll_number    = form.roll_number.data,
            admission_year = form.admission_year.data,
            program_type   = form.program_type.data,
            semester       = form.semester.data,
        )
        if error:
            flash(error, 'danger')
        else:
            flash(f'Student {user.full_name} enrolled successfully.', 'success')
            return redirect(url_for('hod.list_students'))
    return render_template('hod/create_student.html',
                           form=form, title='Enroll Student')


@hod_bp.route('/students/<int:student_id>/delete', methods=['GET', 'POST'])
@login_required
@hod_required
@hod_owns_student
def delete_student(student_id):
    """
    Soft-delete a student WITH a mandatory reason.
    @hod_owns_student pre-fetches and verifies department ownership.
    """
    student = g.owned_student
    form    = DeleteStudentForm()

    if form.validate_on_submit():
        success, error = soft_delete_student(
            current_user, student_id, form.reason.data
        )
        if error:
            flash(error, 'danger')
        else:
            flash(
                f'{student.full_name} has been removed. '
                f'Their academic records are preserved.',
                'success'
            )
            return redirect(url_for('hod.list_students'))

    return render_template('hod/delete_student.html',
                           form=form, student=student,
                           title='Remove Student')


# ══════════════════════════════════════════════════════════════════════
#  SEMESTER PROMOTION
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/students/<int:student_id>/promote', methods=['POST'])
@login_required
@hod_required
@hod_owns_student
@graduation_not_locked
def promote_student(student_id):
    """Promote a single student one semester forward."""
    student, error = promote_single_student(current_user, student_id)
    if error:
        flash(error, 'warning')
    else:
        flash(
            f'{student.full_name} promoted to Semester {student.semester}.',
            'success'
        )
    return redirect(url_for('hod.list_students'))


@hod_bp.route('/students/bulk-promote', methods=['GET', 'POST'])
@login_required
@hod_required
def bulk_promote_view():
    """
    Bulk promotion form.
    HOD picks: program_type + from_semester → all eligible students promoted.
    """
    form = BulkPromoteForm()
    result = None

    if form.validate_on_submit():
        result = bulk_promote(
            hod_user      = current_user,
            from_semester = form.from_semester.data,
            program_type  = form.program_type.data,
        )
        if 'error' in result:
            flash(result['error'], 'danger')
            result = None
        else:
            flash(result['message'],
                  'success' if result['promoted'] > 0 else 'info')

    return render_template('hod/bulk_promote.html',
                           form=form, result=result,
                           title='Bulk Semester Promotion')


# ══════════════════════════════════════════════════════════════════════
#  GRADUATION (kept from Step 5, uses decorators from Step 5)
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/students/<int:student_id>/graduate', methods=['GET', 'POST'])
@login_required
@hod_required
@hod_owns_student
def graduate_student(student_id):
    """
    Graduate a single student.
    GET  → show confirmation form with student details
    POST → validate form, call graduation_service, redirect

    Note: decorators @graduation_not_locked and @can_graduate_check
    from Step 5 have been REMOVED here because the graduation_service
    now handles all those validations internally — single source of truth.
    The service returns a clear error message if any rule is violated.
    """
    from app.services.graduation_service import graduate_student as svc_graduate
    from app.forms.graduation_forms import GraduateStudentForm

    student = g.owned_student
    form    = GraduateStudentForm()

    if form.validate_on_submit():
        graduated, error = svc_graduate(
            hod_user   = current_user,
            student_id = student_id,
            reason     = form.reason.data
        )
        if error:
            flash(error, 'danger')
            return render_template('hod/graduation/confirm.html',
                                   form=form, student=student,
                                   title='Confirm Graduation')
        flash(
            f'{graduated.full_name} has been graduated successfully '
            f'from {graduated.program_type} Semester {graduated.graduation_semester}. '
            f'Their login has been disabled.',
            'success'
        )
        return redirect(url_for('hod.graduation_management'))

    return render_template('hod/graduation/confirm.html',
                           form=form, student=student,
                           title='Confirm Graduation')


@hod_bp.route('/graduation')
@login_required
@hod_required
def graduation_management():
    """
    Central graduation management page.
    Shows: eligible students, graduated alumni, stats, bulk graduate option.
    """
    from app.services.graduation_service import (
        get_graduation_eligible_students,
        get_graduated_students,
        get_graduation_stats
    )
    eligible   = get_graduation_eligible_students(current_user)
    alumni     = get_graduated_students(current_user)
    stats      = get_graduation_stats(current_user)
    return render_template('hod/graduation/management.html',
                           eligible=eligible,
                           alumni=alumni,
                           stats=stats,
                           title='Graduation Management')


@hod_bp.route('/graduation/alumni')
@login_required
@hod_required
def alumni_list():
    """View all graduated students with filters."""
    from app.services.graduation_service import get_graduated_students
    program_type = request.args.get('program_type')
    year         = request.args.get('year')
    alumni       = get_graduated_students(current_user,
                                          program_type=program_type,
                                          year=year)
    return render_template('hod/graduation/alumni.html',
                           alumni=alumni,
                           selected_pt=program_type,
                           selected_year=year,
                           title='Alumni Records')


@hod_bp.route('/graduation/bulk', methods=['GET', 'POST'])
@login_required
@hod_required
def bulk_graduate_view():
    """Graduate an entire batch at once."""
    from app.services.graduation_service import bulk_graduate
    from app.forms.graduation_forms import BulkGraduateForm
    form   = BulkGraduateForm()
    result = None

    if form.validate_on_submit():
        result = bulk_graduate(
            hod_user     = current_user,
            program_type = form.program_type.data,
            semester     = form.semester.data,
            reason       = form.reason.data,
        )
        if 'error' in result:
            flash(result['error'], 'danger')
            result = None
        else:
            flash(result['message'],
                  'success' if result['graduated'] > 0 else 'info')

    return render_template('hod/graduation/bulk.html',
                           form=form, result=result,
                           title='Bulk Graduation')


# ══════════════════════════════════════════════════════════════════════
#  ATTENDANCE EDITING (from Step 5)
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/attendance/<int:attendance_id>/edit', methods=['GET', 'POST'])
@login_required
@hod_required
@hod_owns_attendance
def edit_attendance(attendance_id):
    from app import db
    record = g.owned_attendance

    if request.method == 'POST':
        new_status = request.form.get('status')
        reason     = request.form.get('reason', '').strip()

        if not reason:
            flash('A reason is required for editing attendance.', 'danger')
        elif new_status not in ('present', 'absent', 'late', 'excused'):
            flash('Invalid status.', 'danger')
        else:
            record.apply_hod_edit(new_status, reason, current_user.teacher_profile)
            db.session.commit()
            flash('Attendance record updated.', 'success')
            return redirect(url_for('hod.dashboard'))

    return render_template('hod/edit_attendance.html',
                           record=record, title='Edit Attendance')