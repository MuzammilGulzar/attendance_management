# # # # """
# # # # TEACHER ROUTES
# # # # ==============
# # # # Teachers can view their subjects, mark attendance, and see history.
# # # # They CANNOT edit any existing record — that is HOD-only.

# # # # All routes use @login_required + @teacher_required minimum.
# # # # Attendance-related routes also use @teacher_owns_subject (Layer 3).
# # # # """

# # # # from datetime import date
# # # # from flask import (Blueprint, render_template, redirect,
# # # #                    url_for, flash, request, g)
# # # # from flask_login import login_required, current_user

# # # # from app.decorators import teacher_required, teacher_owns_subject
# # # # from app.services.teacher_service import (
# # # #     get_teacher_dashboard_data,
# # # #     get_attendance_session,
# # # #     mark_attendance,
# # # #     get_subject_attendance_history,
# # # #     get_student_subject_attendance,
# # # #     STATUS_LABELS, STATUS_COLORS, VALID_STATUSES,
# # # # )

# # # # teacher_bp = Blueprint('teacher', __name__)


# # # # # ══════════════════════════════════════════════════════════════════════
# # # # #  DASHBOARD
# # # # # ══════════════════════════════════════════════════════════════════════

# # # # @teacher_bp.route('/dashboard')
# # # # @login_required
# # # # @teacher_required
# # # # def dashboard():
# # # #     """
# # # #     Teacher's home page.
# # # #     Shows all assigned subjects with today's attendance status.
# # # #     Green checkmark = already marked today. Red dot = not yet marked.
# # # #     """
# # # #     data = get_teacher_dashboard_data(current_user)
# # # #     return render_template('teacher/dashboard.html',
# # # #                            title='Teacher Dashboard', data=data)


# # # # # ══════════════════════════════════════════════════════════════════════
# # # # #  STUDENTS IN A SUBJECT
# # # # #  "Add students to semester" — in our model, students are NOT manually
# # # # #  added to subjects. They are enrolled in a department+semester and
# # # # #  automatically belong to all subjects of that semester.
# # # # #  This view shows the teacher exactly who is in their class.
# # # # # ══════════════════════════════════════════════════════════════════════

# # # # @teacher_bp.route('/subject/<int:subject_id>/students')
# # # # @login_required
# # # # @teacher_required
# # # # @teacher_owns_subject
# # # # def subject_students(subject_id):
# # # #     """
# # # #     Show all students enrolled in this subject's semester.
# # # #     Also shows per-student attendance % for this subject.
# # # #     """
# # # #     subject  = g.owned_subject
# # # #     from app.services.teacher_service import _get_enrolled_students
# # # #     students = _get_enrolled_students(subject)

# # # #     student_rows = []
# # # #     for student in students:
# # # #         pct = student.attendance_percentage_for_subject(subject.id)
# # # #         student_rows.append({
# # # #             'student': student,
# # # #             'pct'    : pct,
# # # #             'low_att': pct < 75 and pct > 0,
# # # #         })

# # # #     return render_template('teacher/subject_students.html',
# # # #                            subject=subject,
# # # #                            student_rows=student_rows,
# # # #                            title=f'{subject.code} — Students')


# # # # # ══════════════════════════════════════════════════════════════════════
# # # # #  MARK ATTENDANCE
# # # # # ══════════════════════════════════════════════════════════════════════

# # # # @teacher_bp.route('/attendance/mark/<int:subject_id>',
# # # #                   methods=['GET', 'POST'])
# # # # @login_required
# # # # @teacher_required
# # # # @teacher_owns_subject
# # # # def mark_attendance_view(subject_id):
# # # #     """
# # # #     GET  → show the attendance form for today (or selected date)
# # # #     POST → validate and save attendance records

# # # #     Key behaviours:
# # # #       - Default date is TODAY
# # # #       - Teacher can select a past date (up to 7 days) for backfill
# # # #       - If attendance already fully marked for chosen date → show
# # # #         read-only view with message to contact HOD for edits
# # # #       - One record per student per subject per date — duplicates
# # # #         are silently skipped (DB constraint + service check)
# # # #     """
# # # #     subject = g.owned_subject

# # # #     # Parse date from query param or form
# # # #     raw_date = request.args.get('date') or request.form.get('mark_date')
# # # #     try:
# # # #         mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
# # # #     except ValueError:
# # # #         mark_date = date.today()

# # # #     if request.method == 'POST':
# # # #         # Build status_map from form: {student_id (int): status (str)}
# # # #         status_map = {}
# # # #         for key, value in request.form.items():
# # # #             if key.startswith('status_'):
# # # #                 try:
# # # #                     sid = int(key.split('_', 1)[1])
# # # #                     status_map[sid] = value
# # # #                 except (ValueError, IndexError):
# # # #                     continue

# # # #         if not status_map:
# # # #             flash('No attendance data received. Please try again.', 'danger')
# # # #             return redirect(url_for('teacher.mark_attendance_view',
# # # #                                     subject_id=subject_id))

# # # #         result = mark_attendance(
# # # #             teacher_user = current_user,
# # # #             subject_id   = subject_id,
# # # #             status_map   = status_map,
# # # #             mark_date    = mark_date,
# # # #         )

# # # #         if 'error' in result:
# # # #             flash(result['error'], 'danger')
# # # #         else:
# # # #             flash(result['message'], 'success')
# # # #             return redirect(url_for('teacher.dashboard'))

# # # #     # GET — prepare session data
# # # #     session_data, error = get_attendance_session(
# # # #         teacher_user = current_user,
# # # #         subject_id   = subject_id,
# # # #         for_date     = mark_date,
# # # #     )

# # # #     if error:
# # # #         flash(error, 'danger')
# # # #         return redirect(url_for('teacher.dashboard'))

# # # #     return render_template('teacher/mark_attendance.html',
# # # #                            session=session_data,
# # # #                            subject=subject,
# # # #                            mark_date=mark_date,
# # # #                            title=f'Attendance — {subject.code}')


# # # # # ══════════════════════════════════════════════════════════════════════
# # # # #  ATTENDANCE HISTORY FOR A SUBJECT
# # # # # ══════════════════════════════════════════════════════════════════════

# # # # @teacher_bp.route('/attendance/history/<int:subject_id>')
# # # # @login_required
# # # # @teacher_required
# # # # @teacher_owns_subject
# # # # def attendance_history(subject_id):
# # # #     """
# # # #     Show the last 30 attendance sessions for this subject.
# # # #     Read-only — teachers can view but not edit.
# # # #     Edit option shows 'Contact HOD' instead of an edit button.
# # # #     """
# # # #     subject = g.owned_subject
# # # #     history = get_subject_attendance_history(current_user, subject_id)

# # # #     return render_template('teacher/attendance_history.html',
# # # #                            subject=subject,
# # # #                            history=history,
# # # #                            status_colors=STATUS_COLORS,
# # # #                            status_labels=STATUS_LABELS,
# # # #                            title=f'{subject.code} — History')


# # # # # ══════════════════════════════════════════════════════════════════════
# # # # #  STUDENT DETAIL — per-subject attendance for one student
# # # # # ══════════════════════════════════════════════════════════════════════

# # # # @teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
# # # # @login_required
# # # # @teacher_required
# # # # @teacher_owns_subject
# # # # def student_attendance_detail(subject_id, student_id):
# # # #     """
# # # #     Show one student's complete attendance record in this subject.
# # # #     Read-only view.
# # # #     """
# # # #     from app.models import Student
# # # #     subject = g.owned_subject
# # # #     student = Student.query.get_or_404(student_id)
# # # #     records = get_student_subject_attendance(subject_id, student_id)

# # # #     conducted = [r for r in records if r.status not in ('leave', 'event')]
# # # #     present   = [r for r in conducted if r.status == 'present']
# # # #     pct       = round(len(present)/len(conducted)*100, 1) if conducted else 0.0

# # # #     return render_template('teacher/student_detail.html',
# # # #                            subject=subject,
# # # #                            student=student,
# # # #                            records=records,
# # # #                            conducted=len(conducted),
# # # #                            present_count=len(present),
# # # #                            pct=pct,
# # # #                            status_colors=STATUS_COLORS,
# # # #                            status_labels=STATUS_LABELS,
# # # #                            title=f'{student.roll_number} — {subject.code}')


# # # ############----------updated------------
# # # """
# # # TEACHER ROUTES
# # # ==============
# # # Teachers can view their subjects, mark attendance, and see history.
# # # They CANNOT edit any existing record — that is HOD-only.

# # # All routes use @login_required + @teacher_required minimum.
# # # Attendance-related routes also use @teacher_owns_subject (Layer 3).
# # # """

# # # from datetime import date
# # # from flask import (Blueprint, render_template, redirect,
# # #                    url_for, flash, request, g)
# # # from flask_login import login_required, current_user

# # # from app.decorators import teacher_required, teacher_owns_subject
# # # from app.services.teacher_service import (
# # #     get_teacher_dashboard_data,
# # #     get_attendance_session,
# # #     mark_attendance,
# # #     get_subject_attendance_history,
# # #     get_student_subject_attendance,
# # #     STATUS_LABELS, STATUS_COLORS, VALID_STATUSES,
# # # )

# # # teacher_bp = Blueprint('teacher', __name__)


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  DASHBOARD
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/dashboard')
# # # @login_required
# # # @teacher_required
# # # def dashboard():
# # #     """
# # #     Teacher's home page.
# # #     Shows all assigned subjects with today's attendance status.
# # #     Green checkmark = already marked today. Red dot = not yet marked.
# # #     """
# # #     data = get_teacher_dashboard_data(current_user)
# # #     return render_template('teacher/dashboard.html',
# # #                            title='Teacher Dashboard', data=data)


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  STUDENTS IN A SUBJECT
# # # #  "Add students to semester" — in our model, students are NOT manually
# # # #  added to subjects. They are enrolled in a department+semester and
# # # #  automatically belong to all subjects of that semester.
# # # #  This view shows the teacher exactly who is in their class.
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/subject/<int:subject_id>/students')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def subject_students(subject_id):
# # #     """
# # #     Show all students enrolled in this subject's semester.
# # #     Also shows per-student attendance % for this subject.
# # #     """
# # #     subject  = g.owned_subject
# # #     from app.services.teacher_service import _get_enrolled_students
# # #     students = _get_enrolled_students(subject)

# # #     student_rows = []
# # #     for student in students:
# # #         pct = student.attendance_percentage_for_subject(subject.id)
# # #         student_rows.append({
# # #             'student': student,
# # #             'pct'    : pct,
# # #             'low_att': pct < 75 and pct > 0,
# # #         })

# # #     return render_template('teacher/subject_students.html',
# # #                            subject=subject,
# # #                            student_rows=student_rows,
# # #                            title=f'{subject.code} — Students')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  MARK ATTENDANCE
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/mark/<int:subject_id>',
# # #                   methods=['GET', 'POST'])
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def mark_attendance_view(subject_id):
# # #     """
# # #     GET  → show the attendance form for today (or selected date)
# # #     POST → validate and save attendance records

# # #     Key behaviours:
# # #       - Default date is TODAY
# # #       - Teacher can select a past date (up to 7 days) for backfill
# # #       - If attendance already fully marked for chosen date → show
# # #         read-only view with message to contact HOD for edits
# # #       - One record per student per subject per date — duplicates
# # #         are silently skipped (DB constraint + service check)
# # #     """
# # #     subject = g.owned_subject

# # #     # Parse date from query param or form
# # #     raw_date = request.args.get('date') or request.form.get('mark_date')
# # #     try:
# # #         mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
# # #     except ValueError:
# # #         mark_date = date.today()

# # #     if request.method == 'POST':
# # #         # Build status_map from form: {student_id (int): status (str)}
# # #         status_map = {}
# # #         for key, value in request.form.items():
# # #             if key.startswith('status_'):
# # #                 try:
# # #                     sid = int(key.split('_', 1)[1])
# # #                     status_map[sid] = value
# # #                 except (ValueError, IndexError):
# # #                     continue

# # #         if not status_map:
# # #             flash('No attendance data received. Please try again.', 'danger')
# # #             return redirect(url_for('teacher.mark_attendance_view',
# # #                                     subject_id=subject_id))

# # #         result = mark_attendance(
# # #             teacher_user = current_user,
# # #             subject_id   = subject_id,
# # #             status_map   = status_map,
# # #             mark_date    = mark_date,
# # #         )

# # #         if 'error' in result:
# # #             flash(result['error'], 'danger')
# # #         else:
# # #             flash(result['message'], 'success')
# # #             return redirect(url_for('teacher.dashboard'))

# # #     # GET — prepare session data
# # #     session_data, error = get_attendance_session(
# # #         teacher_user = current_user,
# # #         subject_id   = subject_id,
# # #         for_date     = mark_date,
# # #     )

# # #     if error:
# # #         flash(error, 'danger')
# # #         return redirect(url_for('teacher.dashboard'))

# # #     return render_template('teacher/mark_attendance.html',
# # #                            session=session_data,
# # #                            subject=subject,
# # #                            mark_date=mark_date,
# # #                            title=f'Attendance — {subject.code}')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  ATTENDANCE HISTORY FOR A SUBJECT
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/history/<int:subject_id>')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def attendance_history(subject_id):
# # #     """
# # #     Show the last 30 attendance sessions for this subject.
# # #     Read-only — teachers can view but not edit.
# # #     Edit option shows 'Contact HOD' instead of an edit button.
# # #     """
# # #     subject = g.owned_subject
# # #     history = get_subject_attendance_history(current_user, subject_id)

# # #     return render_template('teacher/attendance_history.html',
# # #                            subject=subject,
# # #                            history=history,
# # #                            status_colors=STATUS_COLORS,
# # #                            status_labels=STATUS_LABELS,
# # #                            title=f'{subject.code} — History')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  STUDENT DETAIL — per-subject attendance for one student
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def student_attendance_detail(subject_id, student_id):
# # #     """
# # #     Show one student's complete attendance record in this subject.
# # #     Read-only view.
# # #     """
# # #     from app.models import Student
# # #     subject = g.owned_subject
# # #     student = Student.query.get_or_404(student_id)
# # #     records = get_student_subject_attendance(subject_id, student_id)

# # #     conducted = [r for r in records if r.status not in ('leave', 'event')]
# # #     present   = [r for r in conducted if r.status == 'present']
# # #     pct       = round(len(present)/len(conducted)*100, 1) if conducted else 0.0

# # #     return render_template('teacher/student_detail.html',
# # #                            subject=subject,
# # #                            student=student,
# # #                            records=records,
# # #                            conducted=len(conducted),
# # #                            present_count=len(present),
# # #                            pct=pct,
# # #                            status_colors=STATUS_COLORS,
# # #                            status_labels=STATUS_LABELS,
# # #                            title=f'{student.roll_number} — {subject.code}')


# # ############3---------updated-------------
# # # """
# # # TEACHER ROUTES
# # # ==============
# # # Teachers can view their subjects, mark attendance, and see history.
# # # They CANNOT edit any existing record — that is HOD-only.

# # # All routes use @login_required + @teacher_required minimum.
# # # Attendance-related routes also use @teacher_owns_subject (Layer 3).
# # # """

# # # from datetime import date
# # # from flask import (Blueprint, render_template, redirect,
# # #                    url_for, flash, request, g)
# # # from flask_login import login_required, current_user
# # # from flask_wtf.csrf import generate_csrf

# # # from app.decorators import teacher_required, teacher_owns_subject
# # # from app.services.teacher_service import (
# # #     get_teacher_dashboard_data,
# # #     get_attendance_session,
# # #     mark_attendance,
# # #     get_subject_attendance_history,
# # #     get_student_subject_attendance,
# # #     STATUS_LABELS, STATUS_COLORS, VALID_STATUSES,
# # # )

# # # teacher_bp = Blueprint('teacher', __name__)


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  DASHBOARD
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/dashboard')
# # # @login_required
# # # @teacher_required
# # # def dashboard():
# # #     """
# # #     Teacher's home page.
# # #     Shows all assigned subjects with today's attendance status.
# # #     Green checkmark = already marked today. Red dot = not yet marked.
# # #     """
# # #     data = get_teacher_dashboard_data(current_user)
# # #     return render_template('teacher/dashboard.html',
# # #                            title='Teacher Dashboard', data=data)


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  STUDENTS IN A SUBJECT
# # # #  "Add students to semester" — in our model, students are NOT manually
# # # #  added to subjects. They are enrolled in a department+semester and
# # # #  automatically belong to all subjects of that semester.
# # # #  This view shows the teacher exactly who is in their class.
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/subject/<int:subject_id>/students')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def subject_students(subject_id):
# # #     """
# # #     Show all students enrolled in this subject's semester.
# # #     Also shows per-student attendance % for this subject.
# # #     """
# # #     subject  = g.owned_subject
# # #     from app.services.teacher_service import _get_enrolled_students
# # #     students = _get_enrolled_students(subject)

# # #     student_rows = []
# # #     for student in students:
# # #         pct = student.attendance_percentage_for_subject(subject.id)
# # #         student_rows.append({
# # #             'student': student,
# # #             'pct'    : pct,
# # #             'low_att': pct < 75 and pct > 0,
# # #         })

# # #     return render_template('teacher/subject_students.html',
# # #                            subject=subject,
# # #                            student_rows=student_rows,
# # #                            title=f'{subject.code} — Students')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  MARK ATTENDANCE
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/mark/<int:subject_id>',
# # #                   methods=['GET', 'POST'])
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def mark_attendance_view(subject_id):
# # #     """
# # #     GET  → show the attendance form for today (or selected date)
# # #     POST → validate and save attendance records

# # #     Key behaviours:
# # #       - Default date is TODAY
# # #       - Teacher can select a past date (up to 7 days) for backfill
# # #       - If attendance already fully marked for chosen date → show
# # #         read-only view with message to contact HOD for edits
# # #       - One record per student per subject per date — duplicates
# # #         are silently skipped (DB constraint + service check)
# # #     """
# # #     subject = g.owned_subject

# # #     # Parse date from query param or form
# # #     raw_date = request.args.get('date') or request.form.get('mark_date')
# # #     try:
# # #         mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
# # #     except ValueError:
# # #         mark_date = date.today()

# # #     if request.method == 'POST':
# # #         # Build status_map from form: {student_id (int): status (str)}
# # #         status_map = {}
# # #         for key, value in request.form.items():
# # #             if key.startswith('status_'):
# # #                 try:
# # #                     sid = int(key.split('_', 1)[1])
# # #                     status_map[sid] = value
# # #                 except (ValueError, IndexError):
# # #                     continue

# # #         if not status_map:
# # #             flash('No attendance data received. Please try again.', 'danger')
# # #             return redirect(url_for('teacher.mark_attendance_view',
# # #                                     subject_id=subject_id))

# # #         result = mark_attendance(
# # #             teacher_user = current_user,
# # #             subject_id   = subject_id,
# # #             status_map   = status_map,
# # #             mark_date    = mark_date,
# # #         )

# # #         if 'error' in result:
# # #             flash(result['error'], 'danger')
# # #         else:
# # #             flash(result['message'], 'success')
# # #             return redirect(url_for('teacher.dashboard'))

# # #     # GET — prepare session data
# # #     session_data, error = get_attendance_session(
# # #         teacher_user = current_user,
# # #         subject_id   = subject_id,
# # #         for_date     = mark_date,
# # #     )

# # #     if error:
# # #         flash(error, 'danger')
# # #         return redirect(url_for('teacher.dashboard'))

# # #     return render_template('teacher/mark_attendance.html',
# # #                            session=session_data,
# # #                            subject=subject,
# # #                            mark_date=mark_date,
# # #                            title=f'Attendance — {subject.code}')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  ATTENDANCE HISTORY FOR A SUBJECT
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/history/<int:subject_id>')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def attendance_history(subject_id):
# # #     """
# # #     Show the last 30 attendance sessions for this subject.
# # #     Read-only — teachers can view but not edit.
# # #     Edit option shows 'Contact HOD' instead of an edit button.
# # #     """
# # #     subject = g.owned_subject
# # #     history = get_subject_attendance_history(current_user, subject_id)

# # #     return render_template('teacher/attendance_history.html',
# # #                            subject=subject,
# # #                            history=history,
# # #                            status_colors=STATUS_COLORS,
# # #                            status_labels=STATUS_LABELS,
# # #                            title=f'{subject.code} — History')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  STUDENT DETAIL — per-subject attendance for one student
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def student_attendance_detail(subject_id, student_id):
# # #     """
# # #     Show one student's complete attendance record in this subject.
# # #     Read-only view.
# # #     """
# # #     from app.models import Student
# # #     subject = g.owned_subject
# # #     student = Student.query.get_or_404(student_id)
# # #     records = get_student_subject_attendance(subject_id, student_id)

# # #     conducted = [r for r in records if r.status not in ('leave', 'event')]
# # #     present   = [r for r in conducted if r.status == 'present']
# # #     pct       = round(len(present)/len(conducted)*100, 1) if conducted else 0.0

# # #     return render_template('teacher/student_detail.html',
# # #                            subject=subject,
# # #                            student=student,
# # #                            records=records,
# # #                            conducted=len(conducted),
# # #                            present_count=len(present),
# # #                            pct=pct,
# # #                            status_colors=STATUS_COLORS,
# # #                            status_labels=STATUS_LABELS,
# # #                            title=f'{student.roll_number} — {subject.code}')

# # # # ══════════════════════════════════════════════════════════════════════
# # # #  TEACHER NOTIFICATIONS
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/notifications')
# # # @login_required
# # # @teacher_required
# # # def notifications_inbox():
# # #     """Teacher's notification inbox."""
# # #     from app.services.notification_service import get_inbox, get_inbox_unread_count
# # #     notifs       = get_inbox(current_user, limit=100)
# # #     unread_count = get_inbox_unread_count(current_user)
# # #     return render_template('teacher/notifications.html',
# # #                            title='My Notifications',
# # #                            notifications=notifs,
# # #                            unread_count=unread_count)


# # # @teacher_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
# # # @login_required
# # # @teacher_required
# # # def mark_notification_read(notif_id):
# # #     """Mark a single notification as read (supports AJAX)."""
# # #     from app.services.notification_service import mark_read
# # #     from flask import jsonify
# # #     success, error = mark_read(current_user, notif_id)
# # #     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
# # #         return jsonify({'ok': success, 'error': error})
# # #     if not success:
# # #         flash(error, 'danger')
# # #     return redirect(url_for('teacher.notifications_inbox'))


# # # @teacher_bp.route('/notifications/mark-all-read', methods=['POST'])
# # # @login_required
# # # @teacher_required
# # # def mark_all_notifications_read():
# # #     """Mark all unread notifications as read."""
# # #     from app.services.notification_service import mark_all_read
# # #     count = mark_all_read(current_user)
# # #     flash(f'{count} notification(s) marked as read.' if count
# # #           else 'All notifications are already read.',
# # #           'success' if count else 'info')
# # #     return redirect(url_for('teacher.notifications_inbox'))


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  QR ATTENDANCE
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/qr/<int:subject_id>', methods=['GET', 'POST'])
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def generate_qr(subject_id):
# # #     """
# # #     GET  → show form to set QR expiry duration
# # #     POST → create QRSession, display QR code
# # #     """
# # #     import qrcode, io, base64
# # #     from datetime import datetime, timedelta
# # #     from app import db
# # #     from app.models.qr_session import QRSession

# # #     subject = g.owned_subject
# # #     teacher = current_user.teacher_profile
# # #     active_session = QRSession.query.filter_by(
# # #         subject_id=subject_id,
# # #         teacher_id=teacher.id,
# # #         is_active=True
# # #     ).order_by(QRSession.created_at.desc()).first()

# # #     # Invalidate if expired
# # #     if active_session and active_session.is_expired:
# # #         active_session.is_active = False
# # #         db.session.commit()
# # #         active_session = None

# # #     qr_image = None

# # #     if request.method == 'POST':
# # #         minutes = int(request.form.get('duration', 10))
# # #         minutes = max(2, min(minutes, 60))  # clamp 2–60 mins

# # #         # Deactivate any previous session for this subject
# # #         QRSession.query.filter_by(
# # #             subject_id=subject_id,
# # #             teacher_id=teacher.id,
# # #             is_active=True
# # #         ).update({'is_active': False})

# # #         session = QRSession(
# # #             subject_id = subject_id,
# # #             teacher_id = teacher.id,
# # #             date       = datetime.utcnow().date(),
# # #             expires_at = datetime.utcnow() + timedelta(minutes=minutes),
# # #         )
# # #         db.session.add(session)
# # #         db.session.commit()
# # #         active_session = session

# # #     if active_session and active_session.is_valid:
# # #         scan_url = url_for('student.scan_qr',
# # #                            token=active_session.token, _external=True)
# # #         img = qrcode.make(scan_url)
# # #         buf = io.BytesIO()
# # #         img.save(buf, format='PNG')
# # #         qr_image = base64.b64encode(buf.getvalue()).decode('utf-8')

# # #     return render_template('teacher/qr_attendance.html',
# # #                            subject=subject,
# # #                            qr_session=active_session,
# # #                            qr_image=qr_image,
# # #                            scrf_token=generate_csrf(),
# # #                            title=f'QR Attendance — {subject.code}')


# # # @teacher_bp.route('/attendance/qr/<int:subject_id>/stop', methods=['POST'])
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def stop_qr(subject_id):
# # #     """Manually deactivate the active QR session."""
# # #     from app import db
# # #     from app.models.qr_session import QRSession

# # #     teacher = current_user.teacher_profile
# # #     QRSession.query.filter_by(
# # #         subject_id=subject_id,
# # #         teacher_id=teacher.id,
# # #         is_active=True
# # #     ).update({'is_active': False})
# # #     db.session.commit()
# # #     flash('QR session stopped.', 'info')
# # #     return redirect(url_for('teacher.generate_qr', subject_id=subject_id))

# # #########-----------updated new--------
# # # """
# # # TEACHER ROUTES
# # # ==============
# # # Teachers can view their subjects, mark attendance, and see history.
# # # They CANNOT edit any existing record — that is HOD-only.

# # # All routes use @login_required + @teacher_required minimum.
# # # Attendance-related routes also use @teacher_owns_subject (Layer 3).

# # # Routes:
# # #   Steps 9-10 : dashboard, subjects, mark attendance, history, student detail
# # #   Step 12    : notifications inbox, mark read
# # #   Step 14    : QR code generation, cancel, status poll
# # # """

# # # from datetime import date
# # # from flask import (Blueprint, render_template, redirect,
# # #                    url_for, flash, request, g, jsonify)
# # # from flask_login import login_required, current_user

# # # from app.decorators import teacher_required, teacher_owns_subject
# # # from app.services.teacher_service import (
# # #     get_teacher_dashboard_data,
# # #     get_attendance_session,
# # #     mark_attendance,
# # #     get_subject_attendance_history,
# # #     get_student_subject_attendance,
# # #     STATUS_LABELS, STATUS_COLORS, VALID_STATUSES,
# # # )

# # # teacher_bp = Blueprint('teacher', __name__)


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  DASHBOARD
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/dashboard')
# # # @login_required
# # # @teacher_required
# # # def dashboard():
# # #     """
# # #     Teacher's home page.
# # #     Shows all assigned subjects with today's attendance status.
# # #     """
# # #     data = get_teacher_dashboard_data(current_user)
# # #     return render_template('teacher/dashboard.html',
# # #                            title='Teacher Dashboard', data=data)


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  STUDENTS IN A SUBJECT
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/subject/<int:subject_id>/students')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def subject_students(subject_id):
# # #     """Show all students enrolled in this subject's semester."""
# # #     subject  = g.owned_subject
# # #     from app.services.teacher_service import _get_enrolled_students
# # #     students = _get_enrolled_students(subject)

# # #     student_rows = []
# # #     for student in students:
# # #         pct = student.attendance_percentage_for_subject(subject.id)
# # #         student_rows.append({
# # #             'student': student,
# # #             'pct'    : pct,
# # #             'low_att': pct < 75 and pct > 0,
# # #         })

# # #     return render_template('teacher/subject_students.html',
# # #                            subject=subject,
# # #                            student_rows=student_rows,
# # #                            title=f'{subject.code} — Students')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  MARK ATTENDANCE
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/mark/<int:subject_id>',
# # #                   methods=['GET', 'POST'])
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def mark_attendance_view(subject_id):
# # #     """
# # #     GET  → show the attendance form for today (or selected date)
# # #     POST → validate and save attendance records
# # #     """
# # #     subject = g.owned_subject

# # #     raw_date = request.args.get('date') or request.form.get('mark_date')
# # #     try:
# # #         mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
# # #     except ValueError:
# # #         mark_date = date.today()

# # #     if request.method == 'POST':
# # #         status_map = {}
# # #         for key, value in request.form.items():
# # #             if key.startswith('status_'):
# # #                 try:
# # #                     sid = int(key.split('_', 1)[1])
# # #                     status_map[sid] = value
# # #                 except (ValueError, IndexError):
# # #                     continue

# # #         if not status_map:
# # #             flash('No attendance data received. Please try again.', 'danger')
# # #             return redirect(url_for('teacher.mark_attendance_view',
# # #                                     subject_id=subject_id))

# # #         result = mark_attendance(
# # #             teacher_user = current_user,
# # #             subject_id   = subject_id,
# # #             status_map   = status_map,
# # #             mark_date    = mark_date,
# # #         )

# # #         if 'error' in result:
# # #             flash(result['error'], 'danger')
# # #         else:
# # #             flash(result['message'], 'success')
# # #             return redirect(url_for('teacher.dashboard'))

# # #     session_data, error = get_attendance_session(
# # #         teacher_user = current_user,
# # #         subject_id   = subject_id,
# # #         for_date     = mark_date,
# # #     )

# # #     if error:
# # #         flash(error, 'danger')
# # #         return redirect(url_for('teacher.dashboard'))

# # #     return render_template('teacher/mark_attendance.html',
# # #                            session=session_data,
# # #                            subject=subject,
# # #                            mark_date=mark_date,
# # #                            title=f'Attendance — {subject.code}')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  ATTENDANCE HISTORY FOR A SUBJECT
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/history/<int:subject_id>')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def attendance_history(subject_id):
# # #     """Last 30 attendance sessions — read-only for teachers."""
# # #     subject = g.owned_subject
# # #     history = get_subject_attendance_history(current_user, subject_id)

# # #     return render_template('teacher/attendance_history.html',
# # #                            subject=subject,
# # #                            history=history,
# # #                            status_colors=STATUS_COLORS,
# # #                            status_labels=STATUS_LABELS,
# # #                            title=f'{subject.code} — History')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  STUDENT DETAIL
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def student_attendance_detail(subject_id, student_id):
# # #     """One student's complete attendance record in this subject."""
# # #     from app.models import Student
# # #     subject = g.owned_subject
# # #     student = Student.query.get_or_404(student_id)
# # #     records = get_student_subject_attendance(subject_id, student_id)

# # #     conducted = [r for r in records if r.status not in ('leave', 'event')]
# # #     present   = [r for r in conducted if r.status == 'present']
# # #     pct       = round(len(present)/len(conducted)*100, 1) if conducted else 0.0

# # #     return render_template('teacher/student_detail.html',
# # #                            subject=subject,
# # #                            student=student,
# # #                            records=records,
# # #                            conducted=len(conducted),
# # #                            present_count=len(present),
# # #                            pct=pct,
# # #                            status_colors=STATUS_COLORS,
# # #                            status_labels=STATUS_LABELS,
# # #                            title=f'{student.roll_number} — {subject.code}')


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  QR CODE ATTENDANCE  (Step 14)
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/generate-qr/<int:subject_id>')
# # # @login_required
# # # @teacher_required
# # # @teacher_owns_subject
# # # def generate_qr(subject_id):
# # #     """
# # #     Generate a QR code for a class session.

# # #     Calls qr_service.create_session() which:
# # #       1. Creates the in-memory session with UUID + 5-min expiry
# # #       2. Generates the PNG image in app/static/qr/<session_id>.png

# # #     The QR encodes the URL: <QR_BASE_URL>/scan/<session_id>
# # #     QR_BASE_URL is read from the environment (default: http://localhost:5000).
# # #     Students scan the QR → their phone opens that URL → attendance marked.
# # #     """
# # #     from app.services.qr_service import create_session, get_time_remaining

# # #     subject = g.owned_subject
# # #     teacher = current_user.teacher_profile

# # #     # create_session also calls generate_qr_image() internally and
# # #     # stores the image path in session['image_path']
# # #     session = create_session(
# # #         teacher_id = teacher.id,
# # #         subject_id = subject.id,
# # #     )

# # #     time_remaining = get_time_remaining(session['session_id'])

# # #     return render_template(
# # #         'teacher/qr_attendance.html',
# # #         title          = f'QR Attendance — {subject.code}',
# # #         subject        = subject,
# # #         session        = session,
# # #         time_remaining = time_remaining,
# # #     )


# # # @teacher_bp.route('/cancel-qr/<session_id>', methods=['POST'])
# # # @login_required
# # # @teacher_required
# # # def cancel_qr(session_id):
# # #     """
# # #     Teacher manually cancels a QR session before it expires.
# # #     POST-only to prevent accidental cancellation via browser prefetch.
# # #     Verifies the session belongs to this teacher before cancelling.
# # #     """
# # #     from app.services.qr_service import (
# # #         get_session, deactivate_session, delete_qr_image
# # #     )

# # #     teacher = current_user.teacher_profile
# # #     sess    = get_session(session_id)

# # #     if sess is None:
# # #         flash('QR session not found or already expired.', 'info')
# # #         return redirect(url_for('teacher.dashboard'))

# # #     if sess['teacher_id'] != teacher.id:
# # #         flash('You can only cancel your own QR sessions.', 'danger')
# # #         return redirect(url_for('teacher.dashboard'))

# # #     deactivate_session(session_id)
# # #     delete_qr_image(session_id)

# # #     flash('QR session cancelled. Students can no longer scan it.', 'success')
# # #     return redirect(url_for('teacher.dashboard'))


# # # @teacher_bp.route('/qr-status/<session_id>')
# # # @login_required
# # # @teacher_required
# # # def qr_status(session_id):
# # #     """
# # #     AJAX endpoint polled every 5 seconds by the QR display page.
# # #     Returns live scan_count, time_remaining, and is_active.

# # #     The page uses this to:
# # #       - Update the "X students scanned" counter
# # #       - Sync the countdown timer with the server
# # #       - Switch to the expired state when time runs out
# # #     """
# # #     from app.services.qr_service import get_session, get_time_remaining

# # #     sess = get_session(session_id)

# # #     if sess is None:
# # #         return jsonify({
# # #             'scan_count'    : 0,
# # #             'time_remaining': 0,
# # #             'is_active'     : False,
# # #         })

# # #     return jsonify({
# # #         'scan_count'    : sess['scan_count'],
# # #         'time_remaining': get_time_remaining(session_id),
# # #         'is_active'     : sess['is_active'],
# # #     })


# # # # ══════════════════════════════════════════════════════════════════════
# # # #  NOTIFICATIONS  (Step 12)
# # # # ══════════════════════════════════════════════════════════════════════

# # # @teacher_bp.route('/notifications')
# # # @login_required
# # # @teacher_required
# # # def notifications_inbox():
# # #     """Teacher's notification inbox."""
# # #     from app.services.notification_service import get_inbox, get_inbox_unread_count
# # #     notifs       = get_inbox(current_user, limit=100)
# # #     unread_count = get_inbox_unread_count(current_user)
# # #     return render_template('teacher/notifications.html',
# # #                            title='My Notifications',
# # #                            notifications=notifs,
# # #                            unread_count=unread_count)


# # # @teacher_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
# # # @login_required
# # # @teacher_required
# # # def mark_notification_read(notif_id):
# # #     """Mark a single notification as read (supports AJAX)."""
# # #     from app.services.notification_service import mark_read
# # #     success, error = mark_read(current_user, notif_id)
# # #     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
# # #         return jsonify({'ok': success, 'error': error})
# # #     if not success:
# # #         flash(error, 'danger')
# # #     return redirect(url_for('teacher.notifications_inbox'))


# # # @teacher_bp.route('/notifications/mark-all-read', methods=['POST'])
# # # @login_required
# # # @teacher_required
# # # def mark_all_notifications_read():
# # #     """Mark all unread notifications as read."""
# # #     from app.services.notification_service import mark_all_read
# # #     count = mark_all_read(current_user)
# # #     flash(f'{count} notification(s) marked as read.' if count
# # #           else 'All notifications are already read.',
# # #           'success' if count else 'info')
# # #     return redirect(url_for('teacher.notifications_inbox'))

# # ##--------------update 5---------------
# """
# TEACHER ROUTES
# ==============
# Teachers can view their subjects, mark attendance, and see history.
# They CANNOT edit any existing record — that is HOD-only.

# All routes use @login_required + @teacher_required minimum.
# Attendance-related routes also use @teacher_owns_subject (Layer 3).

# Routes:
#   Steps 9-10 : dashboard, subjects, mark attendance, history, student detail
#   Step 12    : notifications inbox, mark read
#   Step 14    : QR code generation, cancel, status poll
# """

# from datetime import date
# from flask import (Blueprint, render_template, redirect,
#                    url_for, flash, request, g, jsonify)
# from flask_login import login_required, current_user

# from app.decorators import teacher_required, teacher_owns_subject
# from app.services.teacher_service import (
#     get_teacher_dashboard_data,
#     get_attendance_session,
#     mark_attendance,
#     get_subject_attendance_history,
#     get_student_subject_attendance,
#     STATUS_LABELS, STATUS_COLORS, VALID_STATUSES,
# )

# teacher_bp = Blueprint('teacher', __name__)


# # ══════════════════════════════════════════════════════════════════════
# #  DASHBOARD
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/dashboard')
# @login_required
# @teacher_required
# def dashboard():
#     """
#     Teacher's home page.
#     Shows all assigned subjects with today's attendance status.
#     """
#     data = get_teacher_dashboard_data(current_user)
#     return render_template('teacher/dashboard.html',
#                            title='Teacher Dashboard', data=data)


# # ══════════════════════════════════════════════════════════════════════
# #  STUDENTS IN A SUBJECT
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/subject/<int:subject_id>/students')
# @login_required
# @teacher_required
# @teacher_owns_subject
# def subject_students(subject_id):
#     """Show all students enrolled in this subject's semester."""
#     subject  = g.owned_subject
#     from app.services.teacher_service import _get_enrolled_students
#     students = _get_enrolled_students(subject)

#     student_rows = []
#     for student in students:
#         pct = student.attendance_percentage_for_subject(subject.id)
#         student_rows.append({
#             'student': student,
#             'pct'    : pct,
#             'low_att': pct < 75 and pct > 0,
#         })

#     return render_template('teacher/subject_students.html',
#                            subject=subject,
#                            student_rows=student_rows,
#                            title=f'{subject.code} — Students')


# # ══════════════════════════════════════════════════════════════════════
# #  MARK ATTENDANCE
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/attendance/mark/<int:subject_id>',
#                   methods=['GET', 'POST'])
# @login_required
# @teacher_required
# @teacher_owns_subject
# def mark_attendance_view(subject_id):
#     """
#     GET  → show the attendance form for today (or selected date)
#     POST → validate and save attendance records
#     """
#     subject = g.owned_subject

#     raw_date = request.args.get('date') or request.form.get('mark_date')
#     try:
#         mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
#     except ValueError:
#         mark_date = date.today()

#     if request.method == 'POST':
#         status_map = {}
#         for key, value in request.form.items():
#             if key.startswith('status_'):
#                 try:
#                     sid = int(key.split('_', 1)[1])
#                     status_map[sid] = value
#                 except (ValueError, IndexError):
#                     continue

#         if not status_map:
#             flash('No attendance data received. Please try again.', 'danger')
#             return redirect(url_for('teacher.mark_attendance_view',
#                                     subject_id=subject_id))

#         result = mark_attendance(
#             teacher_user = current_user,
#             subject_id   = subject_id,
#             status_map   = status_map,
#             mark_date    = mark_date,
#         )

#         if 'error' in result:
#             flash(result['error'], 'danger')
#         else:
#             flash(result['message'], 'success')
#             return redirect(url_for('teacher.dashboard'))

#     session_data, error = get_attendance_session(
#         teacher_user = current_user,
#         subject_id   = subject_id,
#         for_date     = mark_date,
#     )

#     if error:
#         flash(error, 'danger')
#         return redirect(url_for('teacher.dashboard'))

#     return render_template('teacher/mark_attendance.html',
#                            session=session_data,
#                            subject=subject,
#                            mark_date=mark_date,
#                            title=f'Attendance — {subject.code}')


# # ══════════════════════════════════════════════════════════════════════
# #  ATTENDANCE HISTORY FOR A SUBJECT
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/attendance/history/<int:subject_id>')
# @login_required
# @teacher_required
# @teacher_owns_subject
# def attendance_history(subject_id):
#     """Last 30 attendance sessions — read-only for teachers."""
#     subject = g.owned_subject
#     history = get_subject_attendance_history(current_user, subject_id)

#     return render_template('teacher/attendance_history.html',
#                            subject=subject,
#                            history=history,
#                            status_colors=STATUS_COLORS,
#                            status_labels=STATUS_LABELS,
#                            title=f'{subject.code} — History')


# # ══════════════════════════════════════════════════════════════════════
# #  STUDENT DETAIL
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
# @login_required
# @teacher_required
# @teacher_owns_subject
# def student_attendance_detail(subject_id, student_id):
#     """One student's complete attendance record in this subject."""
#     from app.models import Student
#     subject = g.owned_subject
#     student = Student.query.get_or_404(student_id)
#     records = get_student_subject_attendance(subject_id, student_id)

#     conducted = [r for r in records if r.status not in ('leave', 'event')]
#     present   = [r for r in conducted if r.status == 'present']
#     pct       = round(len(present)/len(conducted)*100, 1) if conducted else 0.0

#     return render_template('teacher/student_detail.html',
#                            subject=subject,
#                            student=student,
#                            records=records,
#                            conducted=len(conducted),
#                            present_count=len(present),
#                            pct=pct,
#                            status_colors=STATUS_COLORS,
#                            status_labels=STATUS_LABELS,
#                            title=f'{student.roll_number} — {subject.code}')


# # ══════════════════════════════════════════════════════════════════════
# #  QR CODE ATTENDANCE  (Step 14)
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/generate-qr/<int:subject_id>')
# @login_required
# @teacher_required
# @teacher_owns_subject
# def generate_qr(subject_id):
#     """
#     Generate a QR code for a class session.

#     Calls qr_service.create_session() which:
#       1. Creates the in-memory session with UUID + 5-min expiry
#       2. Generates the PNG image in app/static/qr/<session_id>.png

#     The QR encodes the URL: <QR_BASE_URL>/scan/<session_id>
#     QR_BASE_URL is read from the environment (default: http://localhost:5000).
#     Students scan the QR → their phone opens that URL → attendance marked.
#     """
#     from app.services.qr_service import create_session, get_time_remaining

#     subject = g.owned_subject
#     teacher = current_user.teacher_profile

#     # create_session also calls generate_qr_image() internally and
#     # stores the image path in session['image_path']
#     session = create_session(
#         teacher_id = teacher.id,
#         subject_id = subject.id,
#     )

#     time_remaining = get_time_remaining(session['session_id'])

#     return render_template(
#         'teacher/qr_generate.html',
#         title          = f'QR Attendance — {subject.code}',
#         subject        = subject,
#         session        = session,
#         time_remaining = time_remaining,
#     )


# @teacher_bp.route('/cancel-qr/<session_id>', methods=['POST'])
# @login_required
# @teacher_required
# def cancel_qr(session_id):
#     """
#     Teacher manually cancels a QR session before it expires.
#     POST-only to prevent accidental cancellation via browser prefetch.
#     Verifies the session belongs to this teacher before cancelling.
#     """
#     from app.services.qr_service import (
#         get_session, deactivate_session, delete_qr_image
#     )

#     teacher = current_user.teacher_profile
#     sess    = get_session(session_id)

#     if sess is None:
#         flash('QR session not found or already expired.', 'info')
#         return redirect(url_for('teacher.dashboard'))

#     if sess['teacher_id'] != teacher.id:
#         flash('You can only cancel your own QR sessions.', 'danger')
#         return redirect(url_for('teacher.dashboard'))

#     deactivate_session(session_id)
#     delete_qr_image(session_id)

#     flash('QR session cancelled. Students can no longer scan it.', 'success')
#     return redirect(url_for('teacher.dashboard'))


# @teacher_bp.route('/qr-status/<session_id>')
# @login_required
# @teacher_required
# def qr_status(session_id):
#     """
#     AJAX endpoint polled every 5 seconds by the QR display page.
#     Returns live scan_count, time_remaining, and is_active.

#     The page uses this to:
#       - Update the "X students scanned" counter
#       - Sync the countdown timer with the server
#       - Switch to the expired state when time runs out
#     """
#     from app.services.qr_service import get_session, get_time_remaining

#     sess = get_session(session_id)

#     if sess is None:
#         return jsonify({
#             'scan_count'    : 0,
#             'time_remaining': 0,
#             'is_active'     : False,
#         })

#     return jsonify({
#         'scan_count'    : sess['scan_count'],
#         'time_remaining': get_time_remaining(session_id),
#         'is_active'     : sess['is_active'],
#     })


# # ══════════════════════════════════════════════════════════════════════
# #  NOTIFICATIONS  (Step 12)
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/notifications')
# @login_required
# @teacher_required
# def notifications_inbox():
#     """Teacher's notification inbox."""
#     from app.services.notification_service import get_inbox, get_inbox_unread_count
#     notifs       = get_inbox(current_user, limit=100)
#     unread_count = get_inbox_unread_count(current_user)
#     return render_template('teacher/notifications.html',
#                            title='My Notifications',
#                            notifications=notifs,
#                            unread_count=unread_count)


# @teacher_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
# @login_required
# @teacher_required
# def mark_notification_read(notif_id):
#     """Mark a single notification as read (supports AJAX)."""
#     from app.services.notification_service import mark_read
#     success, error = mark_read(current_user, notif_id)
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         return jsonify({'ok': success, 'error': error})
#     if not success:
#         flash(error, 'danger')
#     return redirect(url_for('teacher.notifications_inbox'))


# @teacher_bp.route('/notifications/mark-all-read', methods=['POST'])
# @login_required
# @teacher_required
# def mark_all_notifications_read():
#     """Mark all unread notifications as read."""
#     from app.services.notification_service import mark_all_read
#     count = mark_all_read(current_user)
#     flash(f'{count} notification(s) marked as read.' if count
#           else 'All notifications are already read.',
#           'success' if count else 'info')
#     return redirect(url_for('teacher.notifications_inbox'))



# # ########------------update-----------
# # """
# # TEACHER ROUTES
# # ==============
# # Teachers can view their subjects, mark attendance, and see history.
# # They CANNOT edit any existing record — that is HOD-only.

# # All routes use @login_required + @teacher_required minimum.
# # Attendance-related routes also use @teacher_owns_subject (Layer 3).
# # """

# # from datetime import date
# # from flask import (Blueprint, render_template, redirect,
# #                    url_for, flash, request, g)
# # from flask_login import login_required, current_user

# # from app.decorators import teacher_required, teacher_owns_subject
# # from app.services.teacher_service import (
# #     get_teacher_dashboard_data,
# #     get_attendance_session,
# #     mark_attendance,
# #     get_subject_attendance_history,
# #     get_student_subject_attendance,
# #     STATUS_LABELS, STATUS_COLORS, VALID_STATUSES,
# # )

# # teacher_bp = Blueprint('teacher', __name__)


# # # ══════════════════════════════════════════════════════════════════════
# # #  DASHBOARD
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/dashboard')
# # @login_required
# # @teacher_required
# # def dashboard():
# #     """
# #     Teacher's home page.
# #     Shows all assigned subjects with today's attendance status.
# #     Green checkmark = already marked today. Red dot = not yet marked.
# #     """
# #     data = get_teacher_dashboard_data(current_user)
# #     return render_template('teacher/dashboard.html',
# #                            title='Teacher Dashboard', data=data)


# # # ══════════════════════════════════════════════════════════════════════
# # #  STUDENTS IN A SUBJECT
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/subject/<int:subject_id>/students')
# # @login_required
# # @teacher_required
# # @teacher_owns_subject
# # def subject_students(subject_id):
# #     subject  = g.owned_subject
# #     from app.services.teacher_service import _get_enrolled_students
# #     students = _get_enrolled_students(subject)

# #     student_rows = []
# #     for student in students:
# #         pct = student.attendance_percentage_for_subject(subject.id)
# #         student_rows.append({
# #             'student': student,
# #             'pct'    : pct,
# #             'low_att': pct < 75 and pct > 0,
# #         })

# #     return render_template('teacher/subject_students.html',
# #                            subject=subject,
# #                            student_rows=student_rows,
# #                            title=f'{subject.code} — Students')


# # # ══════════════════════════════════════════════════════════════════════
# # #  MARK ATTENDANCE  (manual — teacher fills in the form)
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/attendance/mark/<int:subject_id>',
# #                   methods=['GET', 'POST'])
# # @login_required
# # @teacher_required
# # @teacher_owns_subject
# # def mark_attendance_view(subject_id):
# #     subject = g.owned_subject

# #     raw_date = request.args.get('date') or request.form.get('mark_date')
# #     try:
# #         mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
# #     except ValueError:
# #         mark_date = date.today()

# #     if request.method == 'POST':
# #         status_map = {}
# #         for key, value in request.form.items():
# #             if key.startswith('status_'):
# #                 try:
# #                     sid = int(key.split('_', 1)[1])
# #                     status_map[sid] = value
# #                 except (ValueError, IndexError):
# #                     continue

# #         if not status_map:
# #             flash('No attendance data received. Please try again.', 'danger')
# #             return redirect(url_for('teacher.mark_attendance_view',
# #                                     subject_id=subject_id))

# #         result = mark_attendance(
# #             teacher_user = current_user,
# #             subject_id   = subject_id,
# #             status_map   = status_map,
# #             mark_date    = mark_date,
# #         )

# #         if 'error' in result:
# #             flash(result['error'], 'danger')
# #         else:
# #             flash(result['message'], 'success')
# #             return redirect(url_for('teacher.dashboard'))

# #     session_data, error = get_attendance_session(
# #         teacher_user = current_user,
# #         subject_id   = subject_id,
# #         for_date     = mark_date,
# #     )

# #     if error:
# #         flash(error, 'danger')
# #         return redirect(url_for('teacher.dashboard'))

# #     return render_template('teacher/mark_attendance.html',
# #                            session=session_data,
# #                            subject=subject,
# #                            mark_date=mark_date,
# #                            title=f'Attendance — {subject.code}')


# # # ══════════════════════════════════════════════════════════════════════
# # #  QR ATTENDANCE  (teacher generates code; students scan to self-mark)
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/qr/generate/<int:subject_id>', methods=['GET', 'POST'])
# # @login_required
# # @teacher_required
# # @teacher_owns_subject
# # def generate_qr(subject_id):
# #     """
# #     GET  → show the QR generation form (expiry picker)
# #     POST → create the QRSession, render QR code image page

# #     The QR code encodes a URL:
# #         https://<host>/student/scan?token=<uuid>

# #     Students scan this URL with their phone. If they aren't logged in,
# #     Flask-Login redirects them to /auth/login?next=<scan_url>, and after
# #     login they're brought straight back to complete the attendance mark.
# #     """
# #     from app.services.qr_service import generate_qr_session

# #     subject = g.owned_subject

# #     if request.method == 'POST':
# #         try:
# #             expiry_minutes = int(request.form.get('expiry_minutes', 15))
# #             expiry_minutes = max(5, min(expiry_minutes, 60))   # clamp 5–60
# #         except (TypeError, ValueError):
# #             expiry_minutes = 15

# #         # Build the base URL so the QR points to the right host
# #         # Works on both LAN (192.168.x.x:5000) and production domains
# #         base_url = request.host_url.rstrip('/')

# #         qr_session, qr_image_url, error = generate_qr_session(
# #             teacher_user   = current_user,
# #             subject_id     = subject_id,
# #             expiry_minutes = expiry_minutes,
# #             base_url       = base_url,
# #         )

# #         if error:
# #             flash(error, 'danger')
# #             return redirect(url_for('teacher.dashboard'))

# #         return render_template(
# #             'teacher/qr_attendance.html',
# #             subject      = subject,
# #             qr_session   = qr_session,
# #             qr_image_url = qr_image_url,
# #             title        = f'QR Attendance — {subject.code}',
# #         )

# #     # GET — show the form to choose expiry duration
# #     return render_template(
# #         'teacher/qr_generate.html',
# #         subject = subject,
# #         title   = f'Generate QR — {subject.code}',
# #     )


# # @teacher_bp.route('/qr/close/<int:session_id>', methods=['POST'])
# # @login_required
# # @teacher_required
# # def close_qr_session(session_id):
# #     """
# #     Manually deactivate a QR session so students can no longer scan it.
# #     """
# #     from app.services.qr_service import close_qr_session as _close

# #     success, error = _close(current_user, session_id)
# #     if success:
# #         flash('QR session closed. Students can no longer scan this code.', 'info')
# #     else:
# #         flash(error, 'danger')
# #     return redirect(url_for('teacher.dashboard'))


# # # ══════════════════════════════════════════════════════════════════════
# # #  ATTENDANCE HISTORY FOR A SUBJECT
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/attendance/history/<int:subject_id>')
# # @login_required
# # @teacher_required
# # @teacher_owns_subject
# # def attendance_history(subject_id):
# #     subject = g.owned_subject
# #     history = get_subject_attendance_history(current_user, subject_id)

# #     return render_template('teacher/attendance_history.html',
# #                            subject=subject,
# #                            history=history,
# #                            status_colors=STATUS_COLORS,
# #                            status_labels=STATUS_LABELS,
# #                            title=f'{subject.code} — History')


# # # ══════════════════════════════════════════════════════════════════════
# # #  STUDENT DETAIL — per-subject attendance for one student
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
# # @login_required
# # @teacher_required
# # @teacher_owns_subject
# # def student_attendance_detail(subject_id, student_id):
# #     from app.models import Student
# #     subject = g.owned_subject
# #     student = Student.query.get_or_404(student_id)
# #     records = get_student_subject_attendance(subject_id, student_id)

# #     conducted = [r for r in records if r.status not in ('leave', 'event')]
# #     present   = [r for r in conducted if r.status == 'present']
# #     pct       = round(len(present)/len(conducted)*100, 1) if conducted else 0.0

# #     return render_template('teacher/student_detail.html',
# #                            subject=subject,
# #                            student=student,
# #                            records=records,
# #                            conducted=len(conducted),
# #                            present_count=len(present),
# #                            pct=pct,
# #                            status_colors=STATUS_COLORS,
# #                            status_labels=STATUS_LABELS,
# #                            title=f'{student.roll_number} — {subject.code}')


# # # ══════════════════════════════════════════════════════════════════════
# # #  TEACHER NOTIFICATIONS
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/notifications')
# # @login_required
# # @teacher_required
# # def notifications_inbox():
# #     """Teacher's notification inbox."""
# #     from app.services.notification_service import get_inbox, get_inbox_unread_count
# #     notifs       = get_inbox(current_user, limit=100)
# #     unread_count = get_inbox_unread_count(current_user)
# #     return render_template('teacher/notifications.html',
# #                            title='My Notifications',
# #                            notifications=notifs,
# #                            unread_count=unread_count)


# # @teacher_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
# # @login_required
# # @teacher_required
# # def mark_notification_read(notif_id):
# #     """Mark a single notification as read (supports AJAX)."""
# #     from app.services.notification_service import mark_read
# #     from flask import jsonify
# #     success, error = mark_read(current_user, notif_id)
# #     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
# #         return jsonify({'ok': success, 'error': error})
# #     if not success:
# #         flash(error, 'danger')
# #     return redirect(url_for('teacher.notifications_inbox'))


# # @teacher_bp.route('/notifications/mark-all-read', methods=['POST'])
# # @login_required
# # @teacher_required
# # def mark_all_notifications_read():
# #     """Mark all unread notifications as read."""
# #     from app.services.notification_service import mark_all_read
# #     count = mark_all_read(current_user)
# #     flash(f'{count} notification(s) marked as read.' if count
# #           else 'All notifications are already read.',
# #           'success' if count else 'info')
# #     return redirect(url_for('teacher.notifications_inbox'))



##--------------update 5---------------
"""
TEACHER ROUTES
==============
Teachers can view their subjects, mark attendance, and see history.
They CANNOT edit any existing record — that is HOD-only.

All routes use @login_required + @teacher_required minimum.
Attendance-related routes also use @teacher_owns_subject (Layer 3).

Routes:
  Steps 9-10 : dashboard, subjects, mark attendance, history, student detail
  Step 12    : notifications inbox, mark read
  Step 14    : QR code generation, cancel, status poll
"""

from datetime import date
from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, g, jsonify)
from flask_login import login_required, current_user

from app.decorators import teacher_required, teacher_owns_subject
from app.services.teacher_service import (
    get_teacher_dashboard_data,
    get_attendance_session,
    mark_attendance,
    get_subject_attendance_history,
    get_student_subject_attendance,
    STATUS_LABELS, STATUS_COLORS, VALID_STATUSES,
)

teacher_bp = Blueprint('teacher', __name__)


# ══════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    """
    Teacher's home page.
    Shows all assigned subjects with today's attendance status.
    """
    data = get_teacher_dashboard_data(current_user)
    return render_template('teacher/dashboard.html',
                           title='Teacher Dashboard', data=data)


# ══════════════════════════════════════════════════════════════════════
#  STUDENTS IN A SUBJECT
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/subject/<int:subject_id>/students')
@login_required
@teacher_required
@teacher_owns_subject
def subject_students(subject_id):
    """Show all students enrolled in this subject's semester."""
    subject  = g.owned_subject
    from app.services.teacher_service import _get_enrolled_students
    students = _get_enrolled_students(subject)

    student_rows = []
    for student in students:
        pct = student.attendance_percentage_for_subject(subject.id)
        student_rows.append({
            'student': student,
            'pct'    : pct,
            'low_att': pct < 75 and pct > 0,
        })

    return render_template('teacher/subject_students.html',
                           subject=subject,
                           student_rows=student_rows,
                           title=f'{subject.code} — Students')


# ══════════════════════════════════════════════════════════════════════
#  MARK ATTENDANCE
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/attendance/mark/<int:subject_id>',
                  methods=['GET', 'POST'])
@login_required
@teacher_required
@teacher_owns_subject
def mark_attendance_view(subject_id):
    """
    GET  → show the attendance form for today (or selected date)
    POST → validate and save attendance records
    """
    subject = g.owned_subject

    raw_date = request.args.get('date') or request.form.get('mark_date')
    try:
        mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
    except ValueError:
        mark_date = date.today()

    if request.method == 'POST':
        status_map = {}
        for key, value in request.form.items():
            if key.startswith('status_'):
                try:
                    sid = int(key.split('_', 1)[1])
                    status_map[sid] = value
                except (ValueError, IndexError):
                    continue

        if not status_map:
            flash('No attendance data received. Please try again.', 'danger')
            return redirect(url_for('teacher.mark_attendance_view',
                                    subject_id=subject_id))

        result = mark_attendance(
            teacher_user = current_user,
            subject_id   = subject_id,
            status_map   = status_map,
            mark_date    = mark_date,
        )

        if 'error' in result:
            flash(result['error'], 'danger')
        else:
            flash(result['message'], 'success')
            return redirect(url_for('teacher.dashboard'))

    session_data, error = get_attendance_session(
        teacher_user = current_user,
        subject_id   = subject_id,
        for_date     = mark_date,
    )

    if error:
        flash(error, 'danger')
        return redirect(url_for('teacher.dashboard'))

    return render_template('teacher/mark_attendance.html',
                           session=session_data,
                           subject=subject,
                           mark_date=mark_date,
                           title=f'Attendance — {subject.code}')


# ══════════════════════════════════════════════════════════════════════
#  ATTENDANCE HISTORY FOR A SUBJECT
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/attendance/history/<int:subject_id>')
@login_required
@teacher_required
@teacher_owns_subject
def attendance_history(subject_id):
    """Last 30 attendance sessions — read-only for teachers."""
    subject = g.owned_subject
    history = get_subject_attendance_history(current_user, subject_id)

    return render_template('teacher/attendance_history.html',
                           subject=subject,
                           history=history,
                           status_colors=STATUS_COLORS,
                           status_labels=STATUS_LABELS,
                           title=f'{subject.code} — History')


# ══════════════════════════════════════════════════════════════════════
#  STUDENT DETAIL
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
@login_required
@teacher_required
@teacher_owns_subject
def student_attendance_detail(subject_id, student_id):
    """One student's complete attendance record in this subject."""
    from app.models import Student
    subject = g.owned_subject
    student = Student.query.get_or_404(student_id)
    records = get_student_subject_attendance(subject_id, student_id)

    conducted = [r for r in records if r.status not in ('leave', 'event')]
    present   = [r for r in conducted if r.status == 'present']
    pct       = round(len(present)/len(conducted)*100, 1) if conducted else 0.0

    return render_template('teacher/student_detail.html',
                           subject=subject,
                           student=student,
                           records=records,
                           conducted=len(conducted),
                           present_count=len(present),
                           pct=pct,
                           status_colors=STATUS_COLORS,
                           status_labels=STATUS_LABELS,
                           title=f'{student.roll_number} — {subject.code}')


# ══════════════════════════════════════════════════════════════════════
#  QR CODE ATTENDANCE  (Step 14)
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/generate-qr/<int:subject_id>')
@login_required
@teacher_required
@teacher_owns_subject
def generate_qr(subject_id):
    """
    Generate a QR code for a class session.

    Calls qr_service.create_session() which:
      1. Creates the in-memory session with UUID + 5-min expiry
      2. Generates the PNG image in app/static/qr/<session_id>.png

    The QR encodes the URL: <QR_BASE_URL>/scan/<session_id>
    QR_BASE_URL is read from the environment (default: http://localhost:5000).
    Students scan the QR → their phone opens that URL → attendance marked.
    """
    from app.services.qr_service import create_session, get_time_remaining

    subject = g.owned_subject
    teacher = current_user.teacher_profile

    # create_session also calls generate_qr_image() internally and
    # stores the image path in session['image_path']
    session = create_session(
        teacher_id = teacher.id,
        subject_id = subject.id,
    )

    time_remaining = get_time_remaining(session['session_id'])

    return render_template(
        'teacher/qr_generate.html',
        title          = f'QR Attendance — {subject.code}',
        subject        = subject,
        session        = session,
        time_remaining = time_remaining,
    )


@teacher_bp.route('/cancel-qr/<session_id>', methods=['POST'])
@login_required
@teacher_required
def cancel_qr(session_id):
    """
    Teacher manually cancels a QR session before it expires.
    POST-only to prevent accidental cancellation via browser prefetch.
    Verifies the session belongs to this teacher before cancelling.
    """
    from app.services.qr_service import (
        get_session, deactivate_session, delete_qr_image
    )

    teacher = current_user.teacher_profile
    sess    = get_session(session_id)

    if sess is None:
        flash('QR session not found or already expired.', 'info')
        return redirect(url_for('teacher.dashboard'))

    if sess['teacher_id'] != teacher.id:
        flash('You can only cancel your own QR sessions.', 'danger')
        return redirect(url_for('teacher.dashboard'))

    deactivate_session(session_id)
    delete_qr_image(session_id)

    flash('QR session cancelled. Students can no longer scan it.', 'success')
    return redirect(url_for('teacher.dashboard'))


@teacher_bp.route('/qr-status/<session_id>')
@login_required
@teacher_required
def qr_status(session_id):
    """
    AJAX endpoint polled every 5 seconds by the QR display page.
    Returns live scan_count, time_remaining, and is_active.

    The page uses this to:
      - Update the "X students scanned" counter
      - Sync the countdown timer with the server
      - Switch to the expired state when time runs out
    """
    from app.services.qr_service import get_session, get_time_remaining

    sess = get_session(session_id)

    if sess is None:
        return jsonify({
            'scan_count'    : 0,
            'time_remaining': 0,
            'is_active'     : False,
        })

    return jsonify({
        'scan_count'    : sess['scan_count'],
        'time_remaining': get_time_remaining(session_id),
        'is_active'     : sess['is_active'],
    })


# ══════════════════════════════════════════════════════════════════════
#  NOTIFICATIONS  (Step 12)
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/notifications')
@login_required
@teacher_required
def notifications_inbox():
    """Teacher's notification inbox."""
    from app.services.notification_service import get_inbox, get_inbox_unread_count
    notifs       = get_inbox(current_user, limit=100)
    unread_count = get_inbox_unread_count(current_user)
    return render_template('teacher/notifications.html',
                           title='My Notifications',
                           notifications=notifs,
                           unread_count=unread_count)


@teacher_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
@teacher_required
def mark_notification_read(notif_id):
    """Mark a single notification as read (supports AJAX)."""
    from app.services.notification_service import mark_read
    success, error = mark_read(current_user, notif_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': success, 'error': error})
    if not success:
        flash(error, 'danger')
    return redirect(url_for('teacher.notifications_inbox'))


@teacher_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@teacher_required
def mark_all_notifications_read():
    """Mark all unread notifications as read."""
    from app.services.notification_service import mark_all_read
    count = mark_all_read(current_user)
    flash(f'{count} notification(s) marked as read.' if count
          else 'All notifications are already read.',
          'success' if count else 'info')
    return redirect(url_for('teacher.notifications_inbox'))