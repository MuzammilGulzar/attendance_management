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
# # #  "Add students to semester" — in our model, students are NOT manually
# # #  added to subjects. They are enrolled in a department+semester and
# # #  automatically belong to all subjects of that semester.
# # #  This view shows the teacher exactly who is in their class.
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/subject/<int:subject_id>/students')
# # @login_required
# # @teacher_required
# # @teacher_owns_subject
# # def subject_students(subject_id):
# #     """
# #     Show all students enrolled in this subject's semester.
# #     Also shows per-student attendance % for this subject.
# #     """
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
# # #  MARK ATTENDANCE
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/attendance/mark/<int:subject_id>',
# #                   methods=['GET', 'POST'])
# # @login_required
# # @teacher_required
# # @teacher_owns_subject
# # def mark_attendance_view(subject_id):
# #     """
# #     GET  → show the attendance form for today (or selected date)
# #     POST → validate and save attendance records

# #     Key behaviours:
# #       - Default date is TODAY
# #       - Teacher can select a past date (up to 7 days) for backfill
# #       - If attendance already fully marked for chosen date → show
# #         read-only view with message to contact HOD for edits
# #       - One record per student per subject per date — duplicates
# #         are silently skipped (DB constraint + service check)
# #     """
# #     subject = g.owned_subject

# #     # Parse date from query param or form
# #     raw_date = request.args.get('date') or request.form.get('mark_date')
# #     try:
# #         mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
# #     except ValueError:
# #         mark_date = date.today()

# #     if request.method == 'POST':
# #         # Build status_map from form: {student_id (int): status (str)}
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

# #     # GET — prepare session data
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
# # #  ATTENDANCE HISTORY FOR A SUBJECT
# # # ══════════════════════════════════════════════════════════════════════

# # @teacher_bp.route('/attendance/history/<int:subject_id>')
# # @login_required
# # @teacher_required
# # @teacher_owns_subject
# # def attendance_history(subject_id):
# #     """
# #     Show the last 30 attendance sessions for this subject.
# #     Read-only — teachers can view but not edit.
# #     Edit option shows 'Contact HOD' instead of an edit button.
# #     """
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
# #     """
# #     Show one student's complete attendance record in this subject.
# #     Read-only view.
# #     """
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


# ############----------updated------------
# """
# TEACHER ROUTES
# ==============
# Teachers can view their subjects, mark attendance, and see history.
# They CANNOT edit any existing record — that is HOD-only.

# All routes use @login_required + @teacher_required minimum.
# Attendance-related routes also use @teacher_owns_subject (Layer 3).
# """

# from datetime import date
# from flask import (Blueprint, render_template, redirect,
#                    url_for, flash, request, g)
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
#     Green checkmark = already marked today. Red dot = not yet marked.
#     """
#     data = get_teacher_dashboard_data(current_user)
#     return render_template('teacher/dashboard.html',
#                            title='Teacher Dashboard', data=data)


# # ══════════════════════════════════════════════════════════════════════
# #  STUDENTS IN A SUBJECT
# #  "Add students to semester" — in our model, students are NOT manually
# #  added to subjects. They are enrolled in a department+semester and
# #  automatically belong to all subjects of that semester.
# #  This view shows the teacher exactly who is in their class.
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/subject/<int:subject_id>/students')
# @login_required
# @teacher_required
# @teacher_owns_subject
# def subject_students(subject_id):
#     """
#     Show all students enrolled in this subject's semester.
#     Also shows per-student attendance % for this subject.
#     """
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

#     Key behaviours:
#       - Default date is TODAY
#       - Teacher can select a past date (up to 7 days) for backfill
#       - If attendance already fully marked for chosen date → show
#         read-only view with message to contact HOD for edits
#       - One record per student per subject per date — duplicates
#         are silently skipped (DB constraint + service check)
#     """
#     subject = g.owned_subject

#     # Parse date from query param or form
#     raw_date = request.args.get('date') or request.form.get('mark_date')
#     try:
#         mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
#     except ValueError:
#         mark_date = date.today()

#     if request.method == 'POST':
#         # Build status_map from form: {student_id (int): status (str)}
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

#     # GET — prepare session data
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
#     """
#     Show the last 30 attendance sessions for this subject.
#     Read-only — teachers can view but not edit.
#     Edit option shows 'Contact HOD' instead of an edit button.
#     """
#     subject = g.owned_subject
#     history = get_subject_attendance_history(current_user, subject_id)

#     return render_template('teacher/attendance_history.html',
#                            subject=subject,
#                            history=history,
#                            status_colors=STATUS_COLORS,
#                            status_labels=STATUS_LABELS,
#                            title=f'{subject.code} — History')


# # ══════════════════════════════════════════════════════════════════════
# #  STUDENT DETAIL — per-subject attendance for one student
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
# @login_required
# @teacher_required
# @teacher_owns_subject
# def student_attendance_detail(subject_id, student_id):
#     """
#     Show one student's complete attendance record in this subject.
#     Read-only view.
#     """
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


############3---------updated-------------
"""
TEACHER ROUTES
==============
Teachers can view their subjects, mark attendance, and see history.
They CANNOT edit any existing record — that is HOD-only.

All routes use @login_required + @teacher_required minimum.
Attendance-related routes also use @teacher_owns_subject (Layer 3).
"""

from datetime import date
from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, g)
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
    Green checkmark = already marked today. Red dot = not yet marked.
    """
    data = get_teacher_dashboard_data(current_user)
    return render_template('teacher/dashboard.html',
                           title='Teacher Dashboard', data=data)


# ══════════════════════════════════════════════════════════════════════
#  STUDENTS IN A SUBJECT
#  "Add students to semester" — in our model, students are NOT manually
#  added to subjects. They are enrolled in a department+semester and
#  automatically belong to all subjects of that semester.
#  This view shows the teacher exactly who is in their class.
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/subject/<int:subject_id>/students')
@login_required
@teacher_required
@teacher_owns_subject
def subject_students(subject_id):
    """
    Show all students enrolled in this subject's semester.
    Also shows per-student attendance % for this subject.
    """
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

    Key behaviours:
      - Default date is TODAY
      - Teacher can select a past date (up to 7 days) for backfill
      - If attendance already fully marked for chosen date → show
        read-only view with message to contact HOD for edits
      - One record per student per subject per date — duplicates
        are silently skipped (DB constraint + service check)
    """
    subject = g.owned_subject

    # Parse date from query param or form
    raw_date = request.args.get('date') or request.form.get('mark_date')
    try:
        mark_date = date.fromisoformat(raw_date) if raw_date else date.today()
    except ValueError:
        mark_date = date.today()

    if request.method == 'POST':
        # Build status_map from form: {student_id (int): status (str)}
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

    # GET — prepare session data
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
    """
    Show the last 30 attendance sessions for this subject.
    Read-only — teachers can view but not edit.
    Edit option shows 'Contact HOD' instead of an edit button.
    """
    subject = g.owned_subject
    history = get_subject_attendance_history(current_user, subject_id)

    return render_template('teacher/attendance_history.html',
                           subject=subject,
                           history=history,
                           status_colors=STATUS_COLORS,
                           status_labels=STATUS_LABELS,
                           title=f'{subject.code} — History')


# ══════════════════════════════════════════════════════════════════════
#  STUDENT DETAIL — per-subject attendance for one student
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
@login_required
@teacher_required
@teacher_owns_subject
def student_attendance_detail(subject_id, student_id):
    """
    Show one student's complete attendance record in this subject.
    Read-only view.
    """
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
#  TEACHER NOTIFICATIONS
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
    from flask import jsonify
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
