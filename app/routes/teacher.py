###############------------fix minor bugs-----------
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
#   Step 15    : QR review — pending submissions, confirm final statuses
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
#     get_pending_qr_submissions,
#     review_qr_submissions,
#     STATUS_LABELS, STATUS_COLORS, VALID_STATUSES, REVIEW_STATUSES,
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
#     Shows all assigned subjects with today's attendance status
#     and a pending-review badge for each subject that has QR submissions.
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

#     # Only present + absent count as conducted (not leave/event/no_class/pending)
#     conducted = [r for r in records if r.status in ('present', 'absent')]
#     present   = [r for r in conducted if r.status == 'present']
#     pct       = round(len(present) / len(conducted) * 100, 1) if conducted else 0.0

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
#     Students scan → enter roll number → record created as 'pending'.
#     Teacher then reviews via /review-qr/<subject_id>.
#     """
#     from app.services.qr_service import create_session, get_time_remaining

#     subject = g.owned_subject
#     teacher = current_user.teacher_profile

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
#     """Cancel a QR session before it expires."""
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
#     """AJAX: live scan_count and time_remaining for QR display page."""
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
# #  QR REVIEW  (Step 15)
# #
# #  Flow:
# #    1. Teacher generates QR → students scan → records created as 'pending'
# #    2. Teacher opens /review-qr/<subject_id>
# #       → sees all pending submissions grouped by date
# #    3. Teacher sets each student to: present / leave / event / no_class
# #    4. Teacher submits → review_qr_submissions() confirms all records
# #       → students not in the list are auto-marked absent
# #    5. Attendance % updates for all students
# # ══════════════════════════════════════════════════════════════════════

# @teacher_bp.route('/review-qr/<int:subject_id>', methods=['GET', 'POST'])
# @login_required
# @teacher_required
# @teacher_owns_subject
# def review_qr(subject_id):
#     """
#     GET  — Show all pending QR submissions for this subject.
#            Grouped by date so the teacher reviews one class session
#            at a time.

#     POST — Process the review form for ONE specific date.
#            The form sends:
#              review_date            → which date to review
#              status_<attendance_id> → new status for each pending record

#            After confirming pending records, enrolled students with no
#            record for that date are auto-marked absent.
#     """
#     subject = g.owned_subject

#     if request.method == 'POST':
#         # Parse review date
#         raw_date = request.form.get('review_date', '')
#         try:
#             review_date = date.fromisoformat(raw_date)
#         except ValueError:
#             flash('Invalid review date. Please try again.', 'danger')
#             return redirect(url_for('teacher.review_qr',
#                                     subject_id=subject_id))

#         # Parse status_map: {attendance_id: new_status}
#         status_map = {}
#         for key, value in request.form.items():
#             if key.startswith('status_'):
#                 try:
#                     att_id = int(key.split('_', 1)[1])
#                     status_map[att_id] = value
#                 except (ValueError, IndexError):
#                     continue

#         success, result = review_qr_submissions(
#             teacher_user = current_user,
#             subject_id   = subject_id,
#             review_date  = review_date,
#             status_map   = status_map,
#         )

#         if not success:
#             flash(result, 'danger')
#         else:
#             flash(result['message'], 'success')

#         return redirect(url_for('teacher.review_qr',
#                                 subject_id=subject_id))

#     # GET — load all pending submissions
#     pending_groups = get_pending_qr_submissions(current_user, subject_id)

#     return render_template(
#         'teacher/qr_review.html',
#         title          = f'Review QR — {subject.code}',
#         subject        = subject,
#         pending_groups = pending_groups,
#         review_statuses= REVIEW_STATUSES,
#         status_labels  = STATUS_LABELS,
#         status_colors  = STATUS_COLORS,
#     )


# @teacher_bp.route('/pending-count')
# @login_required
# @teacher_required
# def pending_count():
#     """
#     AJAX endpoint — returns total pending QR submissions for this teacher.
#     Called by the dashboard JS every 30 seconds to keep the badge live.

#     Returns JSON: { "total": 12 }
#     """
#     data = get_teacher_dashboard_data(current_user)
#     return jsonify({'total': data.get('pending_total', 0)})


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


####################
# ---------------------
##################
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
  Step 15    : QR review — pending submissions, confirm final statuses
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
    get_pending_qr_submissions,
    review_qr_submissions,
    STATUS_LABELS, STATUS_COLORS, VALID_STATUSES, REVIEW_STATUSES,
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
    Shows all assigned subjects with today's attendance status
    and a pending-review badge for each subject that has QR submissions.
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

    # Only present + absent count as conducted (not leave/event/no_class/pending)
    conducted = [r for r in records if r.status in ('present', 'absent')]
    present   = [r for r in conducted if r.status == 'present']
    pct       = round(len(present) / len(conducted) * 100, 1) if conducted else 0.0

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
    Students scan → enter roll number → record created as 'pending'.
    Teacher then reviews via /review-qr/<subject_id>.
    """
    from app.services.qr_service import create_session, get_time_remaining

    subject = g.owned_subject
    teacher = current_user.teacher_profile

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
    """Cancel a QR session before it expires."""
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
    """AJAX: live scan_count and time_remaining for QR display page."""
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
#  QR REVIEW  (Step 15)
#
#  Flow:
#    1. Teacher generates QR → students scan → records created as 'pending'
#    2. Teacher opens /review-qr/<subject_id>
#       → sees all pending submissions grouped by date
#    3. Teacher sets each student to: present / leave / event / no_class
#    4. Teacher submits → review_qr_submissions() confirms all records
#       → students not in the list are auto-marked absent
#    5. Attendance % updates for all students
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/review-qr/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
@teacher_owns_subject
def review_qr(subject_id):
    """
    GET  — Show all pending QR submissions for this subject.
           Grouped by date so the teacher reviews one class session
           at a time.

    POST — Process the review form for ONE specific date.
           The form sends:
             review_date            → which date to review
             status_<attendance_id> → new status for each pending record

           After confirming pending records, enrolled students with no
           record for that date are auto-marked absent.
    """
    subject = g.owned_subject

    if request.method == 'POST':
        # Parse review date
        raw_date = request.form.get('review_date', '')
        try:
            review_date = date.fromisoformat(raw_date)
        except ValueError:
            flash('Invalid review date. Please try again.', 'danger')
            return redirect(url_for('teacher.review_qr',
                                    subject_id=subject_id))

        # Parse two maps from the form:
        #   att_<id>  → scanned students   (keyed by attendance record id)
        #   stu_<id>  → non-scanned students (keyed by student id)
        scanned_map     = {}
        not_scanned_map = {}

        for key, value in request.form.items():
            if key.startswith('att_'):
                try:
                    att_id = int(key[4:])
                    scanned_map[att_id] = value
                except (ValueError, IndexError):
                    continue
            elif key.startswith('stu_'):
                try:
                    stu_id = int(key[4:])
                    not_scanned_map[stu_id] = value
                except (ValueError, IndexError):
                    continue

        success, result = review_qr_submissions(
            teacher_user    = current_user,
            subject_id      = subject_id,
            review_date     = review_date,
            scanned_map     = scanned_map,
            not_scanned_map = not_scanned_map,
        )

        if not success:
            flash(result, 'danger')
        else:
            flash(result['message'], 'success')

        return redirect(url_for('teacher.review_qr',
                                subject_id=subject_id))

    # GET — load all pending submissions
    pending_groups = get_pending_qr_submissions(current_user, subject_id)

    return render_template(
        'teacher/qr_review.html',
        title          = f'Review QR — {subject.code}',
        subject        = subject,
        pending_groups = pending_groups,
        review_statuses= REVIEW_STATUSES,
        status_labels  = STATUS_LABELS,
        status_colors  = STATUS_COLORS,
    )


@teacher_bp.route('/pending-count')
@login_required
@teacher_required
def pending_count():
    """
    AJAX endpoint — returns total pending QR submissions for this teacher.
    Called by the dashboard JS every 30 seconds to keep the badge live.

    Returns JSON: { "total": 12 }
    """
    data = get_teacher_dashboard_data(current_user)
    return jsonify({'total': data.get('pending_total', 0)})


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