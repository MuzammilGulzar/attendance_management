############-----------final update
"""
STUDENT ROUTES
==============
Students can only read their OWN data.

Sections:
  1. Dashboard      — overall summary, subject cards, alerts
  2. Subjects       — enrolled subjects with per-subject attendance
  3. Attendance     — detailed records, semester history
  4. Notifications  — inbox, mark read, delete
  5. QR Scan        — PUBLIC route, no login required
                      GET  → show roll number entry form
                      POST → validate roll + mark attendance
"""

from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request, g, jsonify)
from flask_login import login_required, current_user
from app.decorators import student_required, student_owns_record

student_bp = Blueprint('student', __name__)


# ══════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    from app.services.student_service import get_student_dashboard_data
    student = current_user.student_profile
    if not student:
        flash('Student profile not found. Contact admin.', 'danger')
        return redirect(url_for('auth.logout'))
    data = get_student_dashboard_data(student)
    return render_template('student/dashboard.html',
                           title='My Dashboard', data=data)


# ══════════════════════════════════════════════════════════════════════
#  SUBJECTS
# ══════════════════════════════════════════════════════════════════════

@student_bp.route('/subjects')
@login_required
@student_required
def my_subjects():
    from app.services.student_service import get_subjects_with_attendance
    student  = current_user.student_profile
    subjects = get_subjects_with_attendance(student) if student else []
    return render_template('student/subjects.html',
                           title='My Subjects',
                           student=student,
                           subjects=subjects)  # for what-if helper


# ══════════════════════════════════════════════════════════════════════
#  ATTENDANCE
# ══════════════════════════════════════════════════════════════════════

@student_bp.route('/attendance/<int:student_id>')
@login_required
@student_required
@student_owns_record
def view_attendance(student_id):
    from app.services.attendance_service import get_student_attendance_summary
    from app import db
    from app.models.attendance import Attendance
    from collections import defaultdict

    student  = g.owned_student
    semester = request.args.get('semester', type=int, default=student.semester)
    summary  = get_student_attendance_summary(student.id, semester=semester)

    past_sems = (
        db.session.query(Attendance.semester)
        .filter_by(student_id=student.id)
        .distinct()
        .order_by(Attendance.semester.desc())
        .all()
    )
    semester_options = [r[0] for r in past_sems]

    all_records = (
        Attendance.query
        .filter_by(student_id=student.id, semester=semester)
        .order_by(Attendance.date.desc())
        .all()
    )
    records_by_subject = defaultdict(list)
    for r in all_records:
        records_by_subject[r.subject_id].append(r)

    return render_template('student/attendance.html',
                           title='My Attendance',
                           student=student,
                           summary=summary,
                           semester=semester,
                           semester_options=semester_options,
                           records_by_subject=records_by_subject)


# ══════════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════

@student_bp.route('/notifications')
@login_required
@student_required
def notifications():
    from app.services.student_service import get_notifications, get_unread_count
    notifs       = get_notifications(current_user, limit=100)
    unread_count = get_unread_count(current_user)
    return render_template('student/notifications.html',
                           title='My Notifications',
                           notifications=notifs,
                           unread_count=unread_count)


@student_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
@student_required
def mark_notification_read(notif_id):
    from app.services.student_service import mark_notification_read as svc_mark
    success, error = svc_mark(current_user, notif_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'ok': success, 'error': error})
    if not success:
        flash(error, 'danger')
    return redirect(url_for('student.notifications'))


@student_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@student_required
def mark_all_read():
    from app.services.student_service import mark_all_notifications_read
    count = mark_all_notifications_read(current_user)
    flash(f'{count} notification(s) marked as read.' if count
          else 'No unread notifications.',
          'success' if count else 'info')
    return redirect(url_for('student.notifications'))


@student_bp.route('/notifications/<int:notif_id>/delete', methods=['POST'])
@login_required
@student_required
def delete_notification(notif_id):
    from app.services.student_service import delete_notification as svc_delete
    success, error = svc_delete(current_user, notif_id)
    if not success:
        flash(error, 'danger')
    return redirect(url_for('student.notifications'))


# ══════════════════════════════════════════════════════════════════════
#  QR ATTENDANCE SCAN  (Step B — redesigned)
#
#  URL : /scan/<session_id>          (registered at app root, no prefix)
#  Auth: NONE — fully public
#
#  WHY PUBLIC?
#  ───────────
#  The previous version required @login_required which forced students
#  to log in on their phones mid-class before they could scan.
#  This created two problems:
#    • Students who hadn't set up phone login were blocked entirely.
#    • Even students with accounts had to remember passwords on mobile.
#
#  The new design trusts the roll number as identity:
#    • Student scans QR → sees a simple form
#    • Enters roll number + name → attendance marked
#    • No account/password needed on the phone
#
#  SECURITY:
#  ─────────
#    • Roll number must exist in the DB                (prevents random entries)
#    • Student must be enrolled in this subject        (prevents cross-class marking)
#    • QR expires in 5 minutes                         (prevents replay attacks)
#    • Duplicate check prevents double-marking         (one record per student per day)
#    • All validation lives in mark_by_roll_number()   (single source of truth)
# ══════════════════════════════════════════════════════════════════════
# @login_required
# @student_required
# def scan_qr(session_id):
#     """
#     GET  → Validate session, fetch subject info, show the entry form.
#            Student sees: subject name, semester, time remaining.
#            Student enters: roll number + full name.

#     POST → Submit roll number + name to mark_by_roll_number().
#            Redirect to result page on success or error.

#     This function is NOT decorated with @login_required or @student_required.
#     It is registered directly on the app in __init__.py via add_url_rule()
#     so it sits at /scan/<session_id> (no /student/ prefix).
#     """
#     from app.services.qr_service import (
#         get_session_public_info, mark_by_roll_number
#     )
#     from app.models.subject import Subject

#     # ── GET: Show the entry form ──────────────────────────────────────
#     if request.method == 'GET':

#         # get_session_public_info returns None if session doesn't exist
#         # at all (server restart wiped memory), or a dict with is_valid
#         # and error fields if it exists but is expired/cancelled.
#         info = get_session_public_info(session_id)

#         if info is None:
#             # Session not in memory at all
#             return render_template(
#                 'scan/form.html',
#                 valid        = False,
#                 error        = (
#                     'This QR code is no longer valid. '
#                     'Sessions are lost if the server restarts. '
#                     'Please ask your teacher to generate a new QR code.'
#                 ),
#                 session_id   = session_id,
#                 subject      = None,
#                 time_remaining = 0,
#             ), 410   # 410 Gone

#         if not info['is_valid']:
#             # Session exists in memory but is expired or cancelled
#             return render_template(
#                 'scan/form.html',
#                 valid          = False,
#                 error          = info['error'],
#                 session_id     = session_id,
#                 subject        = None,
#                 time_remaining = 0,
#             ), 410

#         # Fetch the subject so the form can display its name/code
#         subject = Subject.query.get(info['subject_id'])

#         return render_template(
#             'scan/form.html',
#             valid          = True,
#             error          = None,
#             session_id     = session_id,
#             subject        = subject,
#             time_remaining = info['time_remaining'],
#         )

#     # ── POST: Process the roll number form ────────────────────────────
#     roll_number = request.form.get('roll_number', '').strip()
#     full_name   = request.form.get('full_name',   '').strip()

#     # Basic client-side-replicating server-side check
#     if not roll_number:
#         # Re-show the form with an inline error
#         info    = get_session_public_info(session_id)
#         subject = Subject.query.get(info['subject_id']) if info else None
#         return render_template(
#             'scan/form.html',
#             valid          = bool(info and info['is_valid']),
#             error          = None,
#             form_error     = 'Please enter your roll number.',
#             session_id     = session_id,
#             subject        = subject,
#             time_remaining = info['time_remaining'] if info else 0,
#             roll_number    = roll_number,
#             full_name      = full_name,
#         ), 422

#     # Hand off all validation and DB work to the service
#     success, payload = mark_by_roll_number(
#         session_id  = session_id,
#         roll_number = roll_number,
#         full_name   = full_name,
#     )

#     if not success:
#         # payload is an error string — re-show form with the error
#         info    = get_session_public_info(session_id)
#         subject = Subject.query.get(info['subject_id']) if info else None
#         return render_template(
#             'scan/form.html',
#             valid          = bool(info and info['is_valid']),
#             error          = None,
#             form_error     = payload,          # payload = error string
#             session_id     = session_id,
#             subject        = subject,
#             time_remaining = info['time_remaining'] if info else 0,
#             roll_number    = roll_number,      # keep what they typed
#             full_name      = full_name,
#         ), 422

#     # Success — payload is a dict with student/subject/date info
#     return render_template(
#         'scan/result.html',
#         title          = 'Attendance Marked',
#         payload        = payload,              # already_marked, names, date…
#     )

# Above scan_qr was suffereing from session replay problem here is the fix
@login_required
@student_required
def scan_qr(session_id):
    """
    GET  → Validate QR session and show confirmation page.
    POST → Mark attendance for the logged-in student only.

    This prevents one student from entering another student's roll number.
    """
    from flask import session as flask_session
    from app.services.qr_service import (
        get_session_public_info,
        mark_by_logged_in_student,
    )
    from app.models.subject import Subject

    # Block same browser/device from opening this QR again after success
    if flask_session.get(f'qr_used_{session_id}'):
        flash('You have already used this QR code.', 'warning')
        return redirect(url_for('student.dashboard'))

    info = get_session_public_info(session_id)

    if info is None:
        return render_template(
            'scan/form.html',
            valid=False,
            error=(
                'This QR code is no longer valid. '
                'Sessions are lost if the server restarts. '
                'Please ask your teacher to generate a new QR code.'
            ),
            session_id=session_id,
            subject=None,
            time_remaining=0,
        ), 410

    if not info['is_valid']:
        return render_template(
            'scan/form.html',
            valid=False,
            error=info['error'],
            session_id=session_id,
            subject=None,
            time_remaining=0,
        ), 410

    subject = Subject.query.get(info['subject_id'])

    # GET: show confirmation page
    if request.method == 'GET':
        return render_template(
            'scan/form.html',
            valid=True,
            error=None,
            session_id=session_id,
            subject=subject,
            time_remaining=info['time_remaining'],
            student=current_user.student_profile,
        )

    # POST: mark attendance for logged-in student only
    student = current_user.student_profile

    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('student.dashboard'))

    success, payload = mark_by_logged_in_student(
        session_id=session_id,
        student=student,
    )

    if not success:
        return render_template(
            'scan/form.html',
            valid=True,
            error=None,
            form_error=payload,
            session_id=session_id,
            subject=subject,
            time_remaining=info['time_remaining'],
            student=student,
        ), 422

    flask_session[f'qr_used_{session_id}'] = True

    return render_template(
        'scan/result.html',
        title='Attendance Marked',
        payload=payload,
    )


# NOTE: scan_qr is registered in app/__init__.py like this:
#   from app.routes.student import scan_qr
#   app.add_url_rule('/scan/<session_id>', 'student.scan_qr',
#                    scan_qr, methods=['GET', 'POST'])