# # """
# # HOD ROUTES
# # ==========
# # All HOD dashboard routes. Thin controllers — logic in hod_service.py.
# # Every route uses @login_required + @hod_required minimum.
# # """

# # from flask import (Blueprint, render_template, redirect,
# #                    url_for, flash, request, g)
# # from flask_login import login_required, current_user

# # from app.decorators import (hod_required, hod_owns_student,
# #                              hod_owns_attendance, graduation_not_locked,
# #                              can_graduate_check)
# # # graduation_service imported inline in graduation routes to avoid circular imports
# # from app.services.hod_service import (
# #     # teacher
# #     create_teacher, update_teacher, deactivate_teacher,
# #     get_dept_teachers, assign_subject_to_teacher,
# #     unassign_subject_from_teacher,
# #     # subject
# #     create_subject, update_subject, deactivate_subject, get_dept_subjects,
# #     # student
# #     create_student, soft_delete_student, get_students_by_semester,
# #     # promotion
# #     promote_single_student, bulk_promote,
# #     # stats
# #     get_hod_dashboard_stats,
# # )
# # from app.forms.hod_forms import (
# #     CreateTeacherForm, EditTeacherForm, AssignSubjectForm,
# #     CreateSubjectForm, EditSubjectForm,
# #     CreateStudentForm, DeleteStudentForm, BulkPromoteForm,
# # )

# # hod_bp = Blueprint('hod', __name__)


# # # ══════════════════════════════════════════════════════════════════════
# # #  DASHBOARD
# # # ══════════════════════════════════════════════════════════════════════

# # @hod_bp.route('/dashboard')
# # @login_required
# # @hod_required
# # def dashboard():
# #     stats = get_hod_dashboard_stats(current_user)
# #     return render_template('hod/dashboard.html',
# #                            title='HOD Dashboard', stats=stats)


# # # ══════════════════════════════════════════════════════════════════════
# # #  TEACHER MANAGEMENT
# # # ══════════════════════════════════════════════════════════════════════

# # @hod_bp.route('/teachers')
# # @login_required
# # @hod_required
# # def list_teachers():
# #     teachers = get_dept_teachers(current_user)
# #     return render_template('hod/teachers.html',
# #                            teachers=teachers, title='My Teachers')


# # @hod_bp.route('/teachers/create', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # def create_teacher_view():
# #     form = CreateTeacherForm()
# #     if form.validate_on_submit():
# #         user, error = create_teacher(
# #             hod_user    = current_user,
# #             first_name  = form.first_name.data,
# #             last_name   = form.last_name.data,
# #             email       = form.email.data,
# #             password    = form.password.data,
# #             employee_id = form.employee_id.data,
# #         )
# #         if error:
# #             flash(error, 'danger')
# #         else:
# #             flash(f'Teacher {user.full_name} created successfully.', 'success')
# #             return redirect(url_for('hod.list_teachers'))
# #     return render_template('hod/create_teacher.html',
# #                            form=form, title='Add Teacher')


# # @hod_bp.route('/teachers/<int:teacher_id>/edit', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # def edit_teacher(teacher_id):
# #     from app.models import Teacher
# #     teacher = Teacher.query.get_or_404(teacher_id)
# #     form = EditTeacherForm(obj=teacher.user)
# #     if request.method == 'GET':
# #         form.employee_id.data = teacher.employee_id

# #     if form.validate_on_submit():
# #         updated, error = update_teacher(
# #             hod_user    = current_user,
# #             teacher_id  = teacher_id,
# #             first_name  = form.first_name.data,
# #             last_name   = form.last_name.data,
# #             employee_id = form.employee_id.data,
# #         )
# #         if error:
# #             flash(error, 'danger')
# #         else:
# #             flash(f'{updated.full_name} updated.', 'success')
# #             return redirect(url_for('hod.list_teachers'))
# #     return render_template('hod/edit_teacher.html',
# #                            form=form, teacher=teacher, title='Edit Teacher')


# # @hod_bp.route('/teachers/<int:teacher_id>/deactivate', methods=['POST'])
# # @login_required
# # @hod_required
# # def deactivate_teacher_view(teacher_id):
# #     success, error = deactivate_teacher(current_user, teacher_id)
# #     if error:
# #         flash(error, 'danger')
# #     else:
# #         flash('Teacher deactivated. Their records are preserved.', 'success')
# #     return redirect(url_for('hod.list_teachers'))


# # @hod_bp.route('/teachers/assign-subject', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # def assign_subject():
# #     hod_teacher = current_user.teacher_profile
# #     dept_id = hod_teacher.department_id if hod_teacher else None
# #     form = AssignSubjectForm(dept_id=dept_id)

# #     if form.validate_on_submit():
# #         success, error = assign_subject_to_teacher(
# #             current_user, form.teacher_id.data, form.subject_id.data
# #         )
# #         if error:
# #             flash(error, 'danger')
# #         else:
# #             flash('Subject assigned successfully.', 'success')
# #             return redirect(url_for('hod.list_teachers'))
# #     return render_template('hod/assign_subject.html',
# #                            form=form, title='Assign Subject to Teacher')


# # @hod_bp.route('/teachers/<int:teacher_id>/unassign/<int:subject_id>',
# #               methods=['POST'])
# # @login_required
# # @hod_required
# # def unassign_subject(teacher_id, subject_id):
# #     success, error = unassign_subject_from_teacher(
# #         current_user, teacher_id, subject_id
# #     )
# #     if error:
# #         flash(error, 'danger')
# #     else:
# #         flash('Subject unassigned.', 'success')
# #     return redirect(url_for('hod.list_teachers'))


# # # ══════════════════════════════════════════════════════════════════════
# # #  SUBJECT MANAGEMENT
# # # ══════════════════════════════════════════════════════════════════════

# # @hod_bp.route('/subjects')
# # @login_required
# # @hod_required
# # def list_subjects():
# #     subjects = get_dept_subjects(current_user)
# #     return render_template('hod/subjects.html',
# #                            subjects=subjects, title='My Subjects')


# # @hod_bp.route('/subjects/create', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # def create_subject_view():
# #     form = CreateSubjectForm()
# #     if form.validate_on_submit():
# #         subject, error = create_subject(
# #             hod_user      = current_user,
# #             name          = form.name.data,
# #             code          = form.code.data,
# #             semester      = form.semester.data,
# #             program_type  = form.program_type.data,
# #             total_classes = form.total_classes.data,
# #         )
# #         if error:
# #             flash(error, 'danger')
# #         else:
# #             flash(f'Subject "{subject.name}" created.', 'success')
# #             return redirect(url_for('hod.list_subjects'))
# #     return render_template('hod/create_subject.html',
# #                            form=form, title='Create Subject')


# # @hod_bp.route('/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # def edit_subject(subject_id):
# #     from app.models import Subject
# #     subject = Subject.query.get_or_404(subject_id)
# #     form = EditSubjectForm(obj=subject)
# #     if form.validate_on_submit():
# #         updated, error = update_subject(
# #             hod_user      = current_user,
# #             subject_id    = subject_id,
# #             name          = form.name.data,
# #             code          = form.code.data,
# #             semester      = form.semester.data,
# #             program_type  = form.program_type.data,
# #             total_classes = form.total_classes.data,
# #         )
# #         if error:
# #             flash(error, 'danger')
# #         else:
# #             flash(f'Subject "{updated.name}" updated.', 'success')
# #             return redirect(url_for('hod.list_subjects'))
# #     return render_template('hod/edit_subject.html',
# #                            form=form, subject=subject, title='Edit Subject')


# # @hod_bp.route('/subjects/<int:subject_id>/deactivate', methods=['POST'])
# # @login_required
# # @hod_required
# # def deactivate_subject_view(subject_id):
# #     success, error = deactivate_subject(current_user, subject_id)
# #     if error:
# #         flash(error, 'danger')
# #     else:
# #         flash('Subject deactivated. Attendance records preserved.', 'success')
# #     return redirect(url_for('hod.list_subjects'))


# # # ══════════════════════════════════════════════════════════════════════
# # #  STUDENT MANAGEMENT
# # # ══════════════════════════════════════════════════════════════════════

# # @hod_bp.route('/students')
# # @login_required
# # @hod_required
# # def list_students():
# #     """
# #     Show students filtered by semester and program_type.
# #     Query params: ?semester=3&program_type=UG
# #     Default: show all active students grouped by semester.
# #     """
# #     semester     = request.args.get('semester', type=int)
# #     program_type = request.args.get('program_type')
# #     students     = get_students_by_semester(
# #         current_user, semester=semester, program_type=program_type
# #     )
# #     stats = get_hod_dashboard_stats(current_user)
# #     return render_template('hod/students.html',
# #                            students=students,
# #                            sem_breakdown=stats.get('sem_breakdown', []),
# #                            selected_sem=semester,
# #                            selected_pt=program_type,
# #                            title='My Students')


# # @hod_bp.route('/students/create', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # def create_student_view():
# #     form = CreateStudentForm()
# #     if form.validate_on_submit():
# #         user, error = create_student(
# #             hod_user       = current_user,
# #             first_name     = form.first_name.data,
# #             last_name      = form.last_name.data,
# #             email          = form.email.data,
# #             password       = form.password.data,
# #             roll_number    = form.roll_number.data,
# #             admission_year = form.admission_year.data,
# #             program_type   = form.program_type.data,
# #             semester       = form.semester.data,
# #         )
# #         if error:
# #             flash(error, 'danger')
# #         else:
# #             flash(f'Student {user.full_name} enrolled successfully.', 'success')
# #             return redirect(url_for('hod.list_students'))
# #     return render_template('hod/create_student.html',
# #                            form=form, title='Enroll Student')


# # @hod_bp.route('/students/<int:student_id>/delete', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # @hod_owns_student
# # def delete_student(student_id):
# #     """
# #     Soft-delete a student WITH a mandatory reason.
# #     @hod_owns_student pre-fetches and verifies department ownership.
# #     """
# #     student = g.owned_student
# #     form    = DeleteStudentForm()

# #     if form.validate_on_submit():
# #         success, error = soft_delete_student(
# #             current_user, student_id, form.reason.data
# #         )
# #         if error:
# #             flash(error, 'danger')
# #         else:
# #             flash(
# #                 f'{student.full_name} has been removed. '
# #                 f'Their academic records are preserved.',
# #                 'success'
# #             )
# #             return redirect(url_for('hod.list_students'))

# #     return render_template('hod/delete_student.html',
# #                            form=form, student=student,
# #                            title='Remove Student')


# # # ══════════════════════════════════════════════════════════════════════
# # #  SEMESTER PROMOTION
# # # ══════════════════════════════════════════════════════════════════════

# # @hod_bp.route('/students/<int:student_id>/promote', methods=['POST'])
# # @login_required
# # @hod_required
# # @hod_owns_student
# # @graduation_not_locked
# # def promote_student(student_id):
# #     """Promote a single student one semester forward."""
# #     student, error = promote_single_student(current_user, student_id)
# #     if error:
# #         flash(error, 'warning')
# #     else:
# #         flash(
# #             f'{student.full_name} promoted to Semester {student.semester}.',
# #             'success'
# #         )
# #     return redirect(url_for('hod.list_students'))


# # @hod_bp.route('/students/bulk-promote', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # def bulk_promote_view():
# #     """
# #     Bulk promotion form.
# #     HOD picks: program_type + from_semester → all eligible students promoted.
# #     """
# #     form = BulkPromoteForm()
# #     result = None

# #     if form.validate_on_submit():
# #         result = bulk_promote(
# #             hod_user      = current_user,
# #             from_semester = form.from_semester.data,
# #             program_type  = form.program_type.data,
# #         )
# #         if 'error' in result:
# #             flash(result['error'], 'danger')
# #             result = None
# #         else:
# #             flash(result['message'],
# #                   'success' if result['promoted'] > 0 else 'info')

# #     return render_template('hod/bulk_promote.html',
# #                            form=form, result=result,
# #                            title='Bulk Semester Promotion')


# # # ══════════════════════════════════════════════════════════════════════
# # #  GRADUATION (kept from Step 5, uses decorators from Step 5)
# # # ══════════════════════════════════════════════════════════════════════

# # @hod_bp.route('/students/<int:student_id>/graduate', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # @hod_owns_student
# # def graduate_student(student_id):
# #     """
# #     Graduate a single student.
# #     GET  → show confirmation form with student details
# #     POST → validate form, call graduation_service, redirect

# #     Note: decorators @graduation_not_locked and @can_graduate_check
# #     from Step 5 have been REMOVED here because the graduation_service
# #     now handles all those validations internally — single source of truth.
# #     The service returns a clear error message if any rule is violated.
# #     """
# #     from app.services.graduation_service import graduate_student as svc_graduate
# #     from app.forms.graduation_forms import GraduateStudentForm

# #     student = g.owned_student
# #     form    = GraduateStudentForm()

# #     if form.validate_on_submit():
# #         graduated, error = svc_graduate(
# #             hod_user   = current_user,
# #             student_id = student_id,
# #             reason     = form.reason.data
# #         )
# #         if error:
# #             flash(error, 'danger')
# #             return render_template('hod/graduation/confirm.html',
# #                                    form=form, student=student,
# #                                    title='Confirm Graduation')
# #         flash(
# #             f'{graduated.full_name} has been graduated successfully '
# #             f'from {graduated.program_type} Semester {graduated.graduation_semester}. '
# #             f'Their login has been disabled.',
# #             'success'
# #         )
# #         return redirect(url_for('hod.graduation_management'))

# #     return render_template('hod/graduation/confirm.html',
# #                            form=form, student=student,
# #                            title='Confirm Graduation')


# # @hod_bp.route('/graduation')
# # @login_required
# # @hod_required
# # def graduation_management():
# #     """
# #     Central graduation management page.
# #     Shows: eligible students, graduated alumni, stats, bulk graduate option.
# #     """
# #     from app.services.graduation_service import (
# #         get_graduation_eligible_students,
# #         get_graduated_students,
# #         get_graduation_stats
# #     )
# #     eligible   = get_graduation_eligible_students(current_user)
# #     alumni     = get_graduated_students(current_user)
# #     stats      = get_graduation_stats(current_user)
# #     return render_template('hod/graduation/management.html',
# #                            eligible=eligible,
# #                            alumni=alumni,
# #                            stats=stats,
# #                            title='Graduation Management')


# # @hod_bp.route('/graduation/alumni')
# # @login_required
# # @hod_required
# # def alumni_list():
# #     """View all graduated students with filters."""
# #     from app.services.graduation_service import get_graduated_students
# #     program_type = request.args.get('program_type')
# #     year         = request.args.get('year')
# #     alumni       = get_graduated_students(current_user,
# #                                           program_type=program_type,
# #                                           year=year)
# #     return render_template('hod/graduation/alumni.html',
# #                            alumni=alumni,
# #                            selected_pt=program_type,
# #                            selected_year=year,
# #                            title='Alumni Records')


# # @hod_bp.route('/graduation/bulk', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # def bulk_graduate_view():
# #     """Graduate an entire batch at once."""
# #     from app.services.graduation_service import bulk_graduate
# #     from app.forms.graduation_forms import BulkGraduateForm
# #     form   = BulkGraduateForm()
# #     result = None

# #     if form.validate_on_submit():
# #         result = bulk_graduate(
# #             hod_user     = current_user,
# #             program_type = form.program_type.data,
# #             semester     = form.semester.data,
# #             reason       = form.reason.data,
# #         )
# #         if 'error' in result:
# #             flash(result['error'], 'danger')
# #             result = None
# #         else:
# #             flash(result['message'],
# #                   'success' if result['graduated'] > 0 else 'info')

# #     return render_template('hod/graduation/bulk.html',
# #                            form=form, result=result,
# #                            title='Bulk Graduation')


# # # ══════════════════════════════════════════════════════════════════════
# # #  ATTENDANCE EDITING (from Step 5)
# # # ══════════════════════════════════════════════════════════════════════

# # @hod_bp.route('/attendance/<int:attendance_id>/edit', methods=['GET', 'POST'])
# # @login_required
# # @hod_required
# # @hod_owns_attendance
# # def edit_attendance(attendance_id):
# #     from app import db
# #     record = g.owned_attendance

# #     if request.method == 'POST':
# #         new_status = request.form.get('status')
# #         reason     = request.form.get('reason', '').strip()

# #         if not reason:
# #             flash('A reason is required for editing attendance.', 'danger')
# #         elif new_status not in ('present', 'absent', 'late', 'excused'):
# #             flash('Invalid status.', 'danger')
# #         else:
# #             record.apply_hod_edit(new_status, reason, current_user.teacher_profile)
# #             db.session.commit()
# #             flash('Attendance record updated.', 'success')
# #             return redirect(url_for('hod.dashboard'))

# #     return render_template('hod/edit_attendance.html',
# #                            record=record, title='Edit Attendance')

# ######-------------updated--------
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
#     from app.models.teacher import Teacher
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
#     from app.models.subject import Subject
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



"""
HOD ROUTES
==========
All HOD dashboard routes. Thin controllers — logic in hod_service.py.
Every route uses @login_required + @hod_required minimum.

Routes added per step:
  Steps 1-8  : dashboard, teachers, subjects, students, promotion, graduation
  Step 10    : attendance search, edit (fixed statuses), audit log
  Step 12    : notifications inbox, send, sent, mark-read, recipients AJAX
"""

from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, g, jsonify)
from flask_login import login_required, current_user

from app.decorators import (hod_required, hod_owns_student,
                             hod_owns_attendance, graduation_not_locked,
                             can_graduate_check)
from app.services.hod_service import (
    create_teacher, update_teacher, deactivate_teacher,
    get_dept_teachers, assign_subject_to_teacher,
    unassign_subject_from_teacher,
    create_subject, update_subject, deactivate_subject, get_dept_subjects,
    create_student, soft_delete_student, get_students_by_semester,
    promote_single_student, bulk_promote,
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
    from app.models import Teacher
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
    from app.models import Subject
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
#  GRADUATION
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/students/<int:student_id>/graduate', methods=['GET', 'POST'])
@login_required
@hod_required
@hod_owns_student
def graduate_student(student_id):
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
            f'{graduated.full_name} graduated from '
            f'{graduated.program_type} Semester {graduated.graduation_semester}. '
            f'Login disabled.',
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
    from app.services.graduation_service import (
        get_graduation_eligible_students,
        get_graduated_students,
        get_graduation_stats
    )
    eligible = get_graduation_eligible_students(current_user)
    alumni   = get_graduated_students(current_user)
    stats    = get_graduation_stats(current_user)
    return render_template('hod/graduation/management.html',
                           eligible=eligible, alumni=alumni,
                           stats=stats, title='Graduation Management')


@hod_bp.route('/graduation/alumni')
@login_required
@hod_required
def alumni_list():
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
#  ATTENDANCE EDITING  (Step 10)
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/attendance/search')
@login_required
@hod_required
def search_attendance():
    """
    Search attendance records by subject, student, date, status.
    No filters submitted → show the empty search page.
    """
    from app.services.attendance_service import search_attendance_records
    from app.models import Subject
    from datetime import date

    hod_teacher = current_user.teacher_profile
    filters     = {}

    subject_id  = request.args.get('subject_id',  type=int)
    student_id  = request.args.get('student_id',  type=int)
    status      = request.args.get('status')
    date_from   = request.args.get('date_from')
    date_to     = request.args.get('date_to')
    edited_only = request.args.get('edited_only') == '1'
    semester    = request.args.get('semester',     type=int)

    if subject_id:  filters['subject_id']  = subject_id
    if student_id:  filters['student_id']  = student_id
    if status:      filters['status']      = status
    if edited_only: filters['edited_only'] = True
    if semester:    filters['semester']    = semester
    if date_from:
        try:    filters['date_from'] = date.fromisoformat(date_from)
        except: pass
    if date_to:
        try:    filters['date_to'] = date.fromisoformat(date_to)
        except: pass

    records  = search_attendance_records(current_user, filters) if filters else []
    subjects = Subject.query.filter_by(
        department_id = hod_teacher.department_id,
        is_active     = True
    ).order_by(Subject.semester, Subject.name).all() if hod_teacher else []

    return render_template('hod/attendance_search.html',
                           records=records, subjects=subjects,
                           filters=filters, subject_id=subject_id,
                           student_id=student_id,
                           selected_status=status,
                           edited_only=edited_only,
                           title='Attendance Records')


@hod_bp.route('/attendance/<int:attendance_id>/edit', methods=['GET', 'POST'])
@login_required
@hod_required
@hod_owns_attendance
def edit_attendance(attendance_id):
    """
    HOD edits an attendance record.
    Valid statuses: present, absent, leave, event  (NOT late/excused).
    A reason of at least 5 characters is required — stored as audit trail.
    """
    from app.services.attendance_service import hod_edit_attendance
    record = g.owned_attendance

    if request.method == 'POST':
        new_status = request.form.get('status', '').strip()
        reason     = request.form.get('reason', '').strip()

        updated, error = hod_edit_attendance(
            hod_user      = current_user,
            attendance_id = attendance_id,
            new_status    = new_status,
            reason        = reason,
        )
        if error:
            flash(error, 'danger')
        else:
            flash(
                f'Attendance updated: {updated.student.full_name} → '
                f'{updated.status.upper()} on '
                f'{updated.date.strftime("%d %b %Y")}. Reason saved.',
                'success'
            )
            return redirect(url_for('hod.search_attendance'))

    return render_template('hod/edit_attendance.html',
                           record=record, title='Edit Attendance')


@hod_bp.route('/attendance/audit-log')
@login_required
@hod_required
def attendance_audit_log():
    """Full audit trail of all attendance edits made in this department."""
    from app.services.attendance_service import get_edit_audit_log
    edits = get_edit_audit_log(current_user)
    return render_template('hod/attendance_audit.html',
                           edits=edits, title='Edit Audit Log')


# ══════════════════════════════════════════════════════════════════════
#  NOTIFICATIONS  (Step 12)
# ══════════════════════════════════════════════════════════════════════

@hod_bp.route('/notifications')
@login_required
@hod_required
def notifications_inbox():
    """HOD's own inbox — notifications they have received."""
    from app.services.notification_service import get_inbox, get_inbox_unread_count
    notifs       = get_inbox(current_user, limit=100)
    unread_count = get_inbox_unread_count(current_user)
    return render_template('hod/notifications/inbox.html',
                           title='My Notifications',
                           notifications=notifs,
                           unread_count=unread_count)


@hod_bp.route('/notifications/send', methods=['GET', 'POST'])
@login_required
@hod_required
def send_notification():
    """
    Compose and send a notification.
    Targets: one student, one teacher, whole semester, all students, all teachers.
    """
    from app.services.notification_service import (
        send_to_user, send_to_semester,
        send_to_all_students, send_to_all_teachers,
    )
    from app.forms.notification_forms import SendNotificationForm
    from app.models import Teacher, Student

    hod_teacher = current_user.teacher_profile
    form        = SendNotificationForm()

    if hod_teacher:
        dept_id  = hod_teacher.department_id
        teachers = Teacher.query.filter_by(
            department_id=dept_id, is_hod=False, is_active=True
        ).all()
        students = (Student.query
                    .filter_by(department_id=dept_id, is_graduated=False)
                    .join(Student.user).filter_by(is_active=True)
                    .all())
        form.recipient_user_id.choices = (
            [(-1, '— select —')] +
            [(t.user_id, f'[Teacher] {t.full_name} ({t.employee_id})')
             for t in teachers] +
            [(s.user_id, f'[Student] {s.full_name} ({s.roll_number})')
             for s in students]
        )

    if form.validate_on_submit():
        t_type = form.target_type.data
        result = None
        error  = None

        if t_type in ('single_student', 'single_teacher'):
            rid = form.recipient_user_id.data
            if not rid or rid == -1:
                flash('Please select a recipient.', 'danger')
                return render_template('hod/notifications/send.html',
                                       form=form, title='Send Notification')
            notif, error = send_to_user(
                current_user, rid,
                form.title.data, form.message.data, form.notif_type.data
            )
            result = 1 if notif else 0

        elif t_type == 'semester':
            result, error = send_to_semester(
                current_user,
                form.semester.data, form.program_type.data,
                form.title.data, form.message.data, form.notif_type.data
            )

        elif t_type == 'all_students':
            result, error = send_to_all_students(
                current_user,
                form.title.data, form.message.data, form.notif_type.data
            )

        elif t_type == 'all_teachers':
            result, error = send_to_all_teachers(
                current_user,
                form.title.data, form.message.data, form.notif_type.data
            )

        if error:
            flash(error, 'danger')
        else:
            flash(f'Notification sent to {result} recipient(s).', 'success')
            return redirect(url_for('hod.sent_notifications'))

    return render_template('hod/notifications/send.html',
                           form=form, title='Send Notification')


@hod_bp.route('/notifications/sent')
@login_required
@hod_required
def sent_notifications():
    """All notifications this HOD has sent, with read/unread status per recipient."""
    from app.services.notification_service import (
        get_sent_notifications, get_sent_summary
    )
    sent    = get_sent_notifications(current_user)
    summary = get_sent_summary(current_user)
    return render_template('hod/notifications/sent.html',
                           sent=sent, summary=summary,
                           title='Sent Notifications')


@hod_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
@hod_required
def mark_notification_read(notif_id):
    """Mark a received notification as read. Supports AJAX."""
    from app.services.notification_service import mark_read
    success, error = mark_read(current_user, notif_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': success, 'error': error})
    if not success:
        flash(error, 'danger')
    return redirect(url_for('hod.notifications_inbox'))


@hod_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@hod_required
def mark_all_notifications_read():
    """Mark all unread received notifications as read."""
    from app.services.notification_service import mark_all_read
    count = mark_all_read(current_user)
    flash(
        f'{count} notification(s) marked as read.' if count
        else 'No unread notifications.',
        'success' if count else 'info'
    )
    return redirect(url_for('hod.notifications_inbox'))


@hod_bp.route('/notifications/recipients')
@login_required
@hod_required
def get_recipients_json():
    """
    AJAX endpoint used by the send form.
    ?target=student → returns all active students in HOD's dept
    ?target=teacher → returns all active teachers in HOD's dept
    """
    from app.models import Teacher, Student
    target  = request.args.get('target')
    hod_t   = current_user.teacher_profile
    if not hod_t:
        return jsonify([])

    dept_id = hod_t.department_id
    data    = []

    if target == 'teacher':
        teachers = Teacher.query.filter_by(
            department_id=dept_id, is_hod=False, is_active=True
        ).all()
        data = [{'id': t.user_id, 'name': f'{t.full_name} ({t.employee_id})'}
                for t in teachers]

    elif target == 'student':
        students = (Student.query
                    .filter_by(department_id=dept_id, is_graduated=False)
                    .join(Student.user).filter_by(is_active=True)
                    .order_by(Student.semester, Student.roll_number)
                    .all())
        data = [{'id': s.user_id,
                 'name': f'{s.full_name} ({s.roll_number}) — Sem {s.semester}'}
                for s in students]

    return jsonify(data)