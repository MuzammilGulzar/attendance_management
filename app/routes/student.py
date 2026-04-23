# # """
# # STUDENT ROUTES
# # ==============
# # Students can only view their OWN data.
# # @student_owns_record prevents any student from viewing another's records.
# # """

# # from flask import Blueprint, render_template, g, redirect, url_for, flash
# # from flask_login import login_required, current_user
# # from app.decorators import student_required, student_owns_record

# # student_bp = Blueprint('student', __name__)


# # @student_bp.route('/dashboard')
# # @login_required
# # @student_required
# # def dashboard():
# #     student = current_user.student_profile
# #     return render_template('student/dashboard.html',
# #                            title='Student Dashboard', student=student)


# # @student_bp.route('/attendance/<int:student_id>')
# # @login_required
# # @student_required              # Layer 2: must be a student
# # @student_owns_record           # Layer 3: must be viewing OWN record
# # def view_attendance(student_id):
# #     """
# #     Student views their own attendance.
# #     If student_id in URL doesn't match logged-in student → 403.
# #     """
# #     from app.models.attendance import Attendance
# #     from app.models.subject import Subject
# #     student  = g.owned_student   # fetched by @student_owns_record
# #     records  = student.attendance_records.order_by(
# #         Attendance.date.desc()
# #     ).all()
# #     return render_template('student/attendance.html',
# #                            student=student, records=records,
# #                            title='My Attendance')

# # ## qr attendance route
# # @student_bp.route('/qr/<string:token>')
# # @login_required
# # @student_required
# # def scan_qr(token):
# #     """
# #     Student lands here after scanning the QR code.
# #     Validates token → marks attendance as 'present'.
# #     """
# #     from datetime import date
# #     from app import db
# #     from app.models.qr_session import QRSession
# #     from app.models.attendance import Attendance

# #     student = current_user.student_profile
# #     qr = QRSession.query.filter_by(token=token).first_or_404()

# #     if not qr.is_valid:
# #         flash('This QR code has expired or is no longer active.', 'danger')
# #         return redirect(url_for('student.dashboard'))

# #     # Check student is enrolled in this subject's semester/dept
# #     subject = qr.subject
# #     if (student.department_id != subject.department_id or
# #             student.semester != subject.semester or
# #             student.program_type != subject.program_type):
# #         flash('You are not enrolled in this subject.', 'danger')
# #         return redirect(url_for('student.dashboard'))

# #     # Prevent duplicate scan
# #     existing = Attendance.query.filter_by(
# #         student_id = student.id,
# #         subject_id = subject.id,
# #         date       = qr.date,
# #     ).first()

# #     if existing:
# #         flash(f'Attendance already recorded for {subject.code} today.', 'info')
# #         return redirect(url_for('student.dashboard'))

# #     record = Attendance(
# #         student_id   = student.id,
# #         subject_id   = subject.id,
# #         marked_by_id = qr.teacher_id,
# #         date         = qr.date,
# #         status       = 'present',
# #         semester     = student.semester,
# #     )
# #     db.session.add(record)
# #     db.session.commit()

# #     flash(f'Attendance marked for {subject.name}!', 'success')
# #     return redirect(url_for('student.dashboard'))



# """
# STUDENT ROUTES
# ==============
# Students can only read their OWN data.
# Three main sections:
#   1. Dashboard   — overall summary of subjects + attendance + alerts
#   2. Subjects    — enrolled subjects with per-subject attendance
#   3. Attendance  — detailed records, semester history
#   4. Notifications — inbox, mark read, mark all read, delete
# """

# from flask import (Blueprint, render_template, redirect,
#                    url_for, flash, request, g, jsonify)
# from flask_login import login_required, current_user
# from app.decorators import student_required, student_owns_record

# student_bp = Blueprint('student', __name__)


# # ══════════════════════════════════════════════════════════════════════
# #  DASHBOARD
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/dashboard')
# @login_required
# @student_required
# def dashboard():
#     """
#     Student home page.
#     Shows: overall attendance %, subject cards, recent notifications,
#     and any low-attendance warnings.
#     """
#     from app.services.student_service import get_student_dashboard_data
#     student = current_user.student_profile
#     if not student:
#         flash('Student profile not found. Contact admin.', 'danger')
#         return redirect(url_for('auth.logout'))

#     data = get_student_dashboard_data(student)
#     return render_template('student/dashboard.html',
#                            title='My Dashboard', data=data)


# # ══════════════════════════════════════════════════════════════════════
# #  SUBJECTS
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/subjects')
# @login_required
# @student_required
# def my_subjects():
#     """
#     Dedicated subjects page — lists all enrolled subjects with
#     per-subject attendance, teachers, and what-if helpers.
#     """
#     from app.services.student_service import get_subjects_with_attendance
#     student  = current_user.student_profile
#     subjects = get_subjects_with_attendance(student) if student else []
#     return render_template('student/subjects.html',
#                            title='My Subjects',
#                            student=student,
#                            subjects=subjects)


# # ══════════════════════════════════════════════════════════════════════
# #  ATTENDANCE
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/attendance/<int:student_id>')
# @login_required
# @student_required
# @student_owns_record
# def view_attendance(student_id):
#     """
#     Full attendance detail — per-subject breakdown with record-by-record
#     history. Supports switching between semesters via query param.
#     """
#     from app.services.attendance_service import get_student_attendance_summary
#     student  = g.owned_student
#     semester = request.args.get('semester', type=int, default=student.semester)
#     summary  = get_student_attendance_summary(student.id, semester=semester)

#     # Build semester options from attendance history
#     from app import db
#     from app.models.attendance import Attendance
#     past_sems = (
#         db.session.query(Attendance.semester)
#         .filter_by(student_id=student.id)
#         .distinct()
#         .order_by(Attendance.semester.desc())
#         .all()
#     )
#     semester_options = [r[0] for r in past_sems]

#     # Pre-fetch per-subject records so the template doesn't need DB calls
#     from app.models.attendance import Attendance as Att
#     from collections import defaultdict

#     all_records = (
#         Att.query
#         .filter_by(student_id=student.id, semester=semester)
#         .order_by(Att.date.desc())
#         .all()
#     )
#     records_by_subject = defaultdict(list)
#     for r in all_records:
#         records_by_subject[r.subject_id].append(r)

#     return render_template('student/attendance.html',
#                            title='My Attendance',
#                            student=student,
#                            summary=summary,
#                            semester=semester,
#                            semester_options=semester_options,
#                            records_by_subject=records_by_subject)


# # ══════════════════════════════════════════════════════════════════════
# #  NOTIFICATIONS
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/notifications')
# @login_required
# @student_required
# def notifications():
#     """
#     Full notifications page — shows all notifications with read/unread state.
#     Unread notifications are highlighted. Most recent first.
#     """
#     from app.services.student_service import get_notifications, get_unread_count
#     notifs       = get_notifications(current_user, limit=100)
#     unread_count = get_unread_count(current_user)
#     return render_template('student/notifications.html',
#                            title='My Notifications',
#                            notifications=notifs,
#                            unread_count=unread_count)


# @student_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
# @login_required
# @student_required
# def mark_notification_read(notif_id):
#     """
#     Mark a single notification as read.
#     Returns JSON if the request is AJAX, otherwise redirects.
#     """
#     from app.services.student_service import mark_notification_read as svc_mark
#     success, error = svc_mark(current_user, notif_id)

#     # AJAX request (called from JavaScript)
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         if success:
#             return jsonify({'ok': True})
#         return jsonify({'ok': False, 'error': error}), 400

#     # Regular form POST
#     if not success:
#         flash(error, 'danger')
#     return redirect(url_for('student.notifications'))


# @student_bp.route('/notifications/mark-all-read', methods=['POST'])
# @login_required
# @student_required
# def mark_all_read():
#     """Mark all unread notifications as read in one action."""
#     from app.services.student_service import mark_all_notifications_read
#     count = mark_all_notifications_read(current_user)
#     if count:
#         flash(f'{count} notification(s) marked as read.', 'success')
#     else:
#         flash('No unread notifications.', 'info')
#     return redirect(url_for('student.notifications'))


# @student_bp.route('/notifications/<int:notif_id>/delete', methods=['POST'])
# @login_required
# @student_required
# def delete_notification(notif_id):
#     """Delete a single read notification."""
#     from app.services.student_service import delete_notification as svc_delete
#     success, error = svc_delete(current_user, notif_id)
#     if not success:
#         flash(error, 'danger')
#     return redirect(url_for('student.notifications'))



##############-------------updated for qr----------
# """
# STUDENT ROUTES
# ==============
# Students can only read their OWN data.
# Three main sections:
#   1. Dashboard   — overall summary of subjects + attendance + alerts
#   2. Subjects    — enrolled subjects with per-subject attendance
#   3. Attendance  — detailed records, semester history
#   4. Notifications — inbox, mark read, mark all read, delete
# """

# from flask import (Blueprint, render_template, redirect,
#                    url_for, flash, request, g, jsonify)
# from flask_login import login_required, current_user
# from app.decorators import student_required, student_owns_record

# student_bp = Blueprint('student', __name__)


# # ══════════════════════════════════════════════════════════════════════
# #  DASHBOARD
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/dashboard')
# @login_required
# @student_required
# def dashboard():
#     """
#     Student home page.
#     Shows: overall attendance %, subject cards, recent notifications,
#     and any low-attendance warnings.
#     """
#     from app.services.student_service import get_student_dashboard_data
#     student = current_user.student_profile
#     if not student:
#         flash('Student profile not found. Contact admin.', 'danger')
#         return redirect(url_for('auth.logout'))

#     data = get_student_dashboard_data(student)
#     return render_template('student/dashboard.html',
#                            title='My Dashboard', data=data)


# # ══════════════════════════════════════════════════════════════════════
# #  SUBJECTS
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/subjects')
# @login_required
# @student_required
# def my_subjects():
#     """
#     Dedicated subjects page — lists all enrolled subjects with
#     per-subject attendance, teachers, and what-if helpers.
#     """
#     from app.services.student_service import get_subjects_with_attendance
#     student  = current_user.student_profile
#     subjects = get_subjects_with_attendance(student) if student else []
#     return render_template('student/subjects.html',
#                            title='My Subjects',
#                            student=student,
#                            subjects=subjects)


# # ══════════════════════════════════════════════════════════════════════
# #  ATTENDANCE
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/attendance/<int:student_id>')
# @login_required
# @student_required
# @student_owns_record
# def view_attendance(student_id):
#     """
#     Full attendance detail — per-subject breakdown with record-by-record
#     history. Supports switching between semesters via query param.
#     """
#     from app.services.attendance_service import get_student_attendance_summary
#     student  = g.owned_student
#     semester = request.args.get('semester', type=int, default=student.semester)
#     summary  = get_student_attendance_summary(student.id, semester=semester)

#     # Build semester options from attendance history
#     from app import db
#     from app.models.attendance import Attendance
#     past_sems = (
#         db.session.query(Attendance.semester)
#         .filter_by(student_id=student.id)
#         .distinct()
#         .order_by(Attendance.semester.desc())
#         .all()
#     )
#     semester_options = [r[0] for r in past_sems]

#     # Pre-fetch per-subject records so the template doesn't need DB calls
#     from app.models.attendance import Attendance as Att
#     from collections import defaultdict

#     all_records = (
#         Att.query
#         .filter_by(student_id=student.id, semester=semester)
#         .order_by(Att.date.desc())
#         .all()
#     )
#     records_by_subject = defaultdict(list)
#     for r in all_records:
#         records_by_subject[r.subject_id].append(r)

#     return render_template('student/attendance.html',
#                            title='My Attendance',
#                            student=student,
#                            summary=summary,
#                            semester=semester,
#                            semester_options=semester_options,
#                            records_by_subject=records_by_subject)


# # ══════════════════════════════════════════════════════════════════════
# #  NOTIFICATIONS
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/notifications')
# @login_required
# @student_required
# def notifications():
#     """
#     Full notifications page — shows all notifications with read/unread state.
#     Unread notifications are highlighted. Most recent first.
#     """
#     from app.services.student_service import get_notifications, get_unread_count
#     notifs       = get_notifications(current_user, limit=100)
#     unread_count = get_unread_count(current_user)
#     return render_template('student/notifications.html',
#                            title='My Notifications',
#                            notifications=notifs,
#                            unread_count=unread_count)


# @student_bp.route('/notifications/<int:notif_id>/read', methods=['POST'])
# @login_required
# @student_required
# def mark_notification_read(notif_id):
#     """
#     Mark a single notification as read.
#     Returns JSON if the request is AJAX, otherwise redirects.
#     """
#     from app.services.student_service import mark_notification_read as svc_mark
#     success, error = svc_mark(current_user, notif_id)

#     # AJAX request (called from JavaScript)
#     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         if success:
#             return jsonify({'ok': True})
#         return jsonify({'ok': False, 'error': error}), 400

#     # Regular form POST
#     if not success:
#         flash(error, 'danger')
#     return redirect(url_for('student.notifications'))


# @student_bp.route('/notifications/mark-all-read', methods=['POST'])
# @login_required
# @student_required
# def mark_all_read():
#     """Mark all unread notifications as read in one action."""
#     from app.services.student_service import mark_all_notifications_read
#     count = mark_all_notifications_read(current_user)
#     if count:
#         flash(f'{count} notification(s) marked as read.', 'success')
#     else:
#         flash('No unread notifications.', 'info')
#     return redirect(url_for('student.notifications'))


# @student_bp.route('/notifications/<int:notif_id>/delete', methods=['POST'])
# @login_required
# @student_required
# def delete_notification(notif_id):
#     """Delete a single read notification."""
#     from app.services.student_service import delete_notification as svc_delete
#     success, error = svc_delete(current_user, notif_id)
#     if not success:
#         flash(error, 'danger')
#     return redirect(url_for('student.notifications'))


# # ══════════════════════════════════════════════════════════════════════
# #  QR ATTENDANCE SCAN  (Step 14.5)
# #  URL: /scan/<session_id>
# #  This route is what the QR code encodes.
# #  The student's phone camera opens this URL after scanning.
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/scan/<session_id>')
# @login_required
# @student_required
# def scan_qr(session_id):
#     """
#     Called when a student scans a QR code with their phone.

#     FLOW:
#       1. @login_required  — if not logged in, redirect to login page.
#                             Flask-Login saves this URL as 'next' so after
#                             login the student is brought straight back here.
#       2. @student_required — only students can scan. A teacher accidentally
#                              scanning gets a 403, not a duplicate record.
#       3. validate_session  — checks the session exists, is active, not expired.
#       4. Enrollment check  — student must be in the subject's dept/sem/program.
#       5. Duplicate check   — already marked today? Show info, don't double-mark.
#       6. mark_attendance   — calls the SAME service used by manual marking.
#                              All existing rules apply (duplicate prevention,
#                              DB unique constraint, low-att notifications).
#       7. increment_scan_count — update the teacher's live counter.
#       8. Render result page — success or specific error message.
#     """
#     from app.services.qr_service import (
#         validate_session, increment_scan_count, get_session
#     )
#     from app.models import Subject, Student, Teacher
#     from app.models.user import User
#     from app.models.attendance import Attendance
#     from app.services.teacher_service import mark_attendance
#     from datetime import date

#     student = current_user.student_profile

#     # ── Step 3: Validate QR session ──────────────────────────────────
#     session, error = validate_session(session_id)
#     if error:
#         return render_template(
#             'student/scan_result.html',
#             success = False,
#             title   = 'QR Scan Failed',
#             heading = 'QR Code Invalid',
#             message = error,
#             icon    = 'x-circle',
#             color   = 'danger',
#         )

#     # ── Step 4: Get subject from session ─────────────────────────────
#     subject = Subject.query.get(session['subject_id'])
#     if not subject:
#         return render_template(
#             'student/scan_result.html',
#             success = False,
#             title   = 'QR Scan Failed',
#             heading = 'Subject Not Found',
#             message = 'The subject linked to this QR code no longer exists.',
#             icon    = 'x-circle',
#             color   = 'danger',
#         )

#     # ── Step 4: Check student is enrolled in this subject ────────────
#     # Enrollment is implicit: student's dept + semester + program_type
#     # must match the subject's dept + semester + program_type.
#     enrolled = (
#         student.department_id == subject.department_id and
#         student.semester      == subject.semester      and
#         student.program_type  == subject.program_type  and
#         not student.is_graduated
#     )

#     if not enrolled:
#         return render_template(
#             'student/scan_result.html',
#             success = False,
#             title   = 'Not Enrolled',
#             heading = 'You Are Not Enrolled',
#             message = (
#                 f'You are not enrolled in {subject.name} ({subject.code}). '
#                 f'This QR is for {subject.program_type} Semester {subject.semester} '
#                 f'students of {subject.department.name}. '
#                 f'You are currently in Semester {student.semester}.'
#             ),
#             icon    = 'person-x',
#             color   = 'warning',
#             subject = subject,
#         )

#     # ── Step 5: Check for duplicate — already marked today? ──────────
#     today = date.today()
#     existing = Attendance.query.filter_by(
#         student_id = student.id,
#         subject_id = subject.id,
#         date       = today,
#     ).first()

#     if existing:
#         return render_template(
#             'student/scan_result.html',
#             success = True,
#             title   = 'Already Marked',
#             heading = 'Already Marked Present',
#             message = (
#                 f'Your attendance for {subject.name} on '
#                 f'{today.strftime("%d %b %Y")} has already been recorded as '
#                 f'<strong>{existing.status.upper()}</strong>. '
#                 f'No duplicate entry was created.'
#             ),
#             icon    = 'check-circle',
#             color   = 'info',
#             subject = subject,
#             student = student,
#         )

#     # ── Step 6: Get the teacher who owns this session ─────────────────
#     # mark_attendance() needs a teacher_user (User object, not Teacher).
#     # The session stores teacher_id (Teacher.id), so we look up their User.
#     teacher_profile = Teacher.query.get(session['teacher_id'])
#     if not teacher_profile:
#         return render_template(
#             'student/scan_result.html',
#             success = False,
#             title   = 'QR Scan Failed',
#             heading = 'Session Error',
#             message = 'Could not find the teacher for this QR session. Please ask your teacher to generate a new QR code.',
#             icon    = 'x-circle',
#             color   = 'danger',
#         )

#     teacher_user = teacher_profile.user

#     # ── Step 7: Mark attendance via existing service ──────────────────
#     # status_map = {student_id: 'present'} — one student, present status.
#     # This calls the SAME mark_attendance() used by manual form marking.
#     # All rules apply: duplicate check, DB constraint, low-att alerts.
#     result = mark_attendance(
#         teacher_user = teacher_user,
#         subject_id   = subject.id,
#         status_map   = {student.id: 'present'},
#         mark_date    = today,
#     )

#     if 'error' in result:
#         # mark_attendance returned an error (e.g. already marked by teacher)
#         return render_template(
#             'student/scan_result.html',
#             success = False,
#             title   = 'Could Not Mark',
#             heading = 'Attendance Not Marked',
#             message = result['error'],
#             icon    = 'exclamation-circle',
#             color   = 'warning',
#             subject = subject,
#         )

#     # ── Step 8: Increment teacher's scan counter ──────────────────────
#     increment_scan_count(session_id)

#     # ── Step 9: Show success ──────────────────────────────────────────
#     return render_template(
#         'student/scan_result.html',
#         success = True,
#         title   = 'Attendance Marked',
#         heading = 'Attendance Marked ✓',
#         message = (
#             f'You have been marked <strong>PRESENT</strong> for '
#             f'<strong>{subject.name}</strong> ({subject.code}) '
#             f'on {today.strftime("%A, %d %b %Y")}.'
#         ),
#         icon    = 'check-circle-fill',
#         color   = 'success',
#         subject = subject,
#         student = student,
#     )


# #######------------update -------------
# """
# STUDENT ROUTES
# ==============
# Students can only view their OWN data.
# @student_owns_record prevents any student from viewing another's records.
# """

# from flask import Blueprint, render_template, redirect, url_for, flash, request, g
# from flask_login import login_required, current_user
# from app.decorators import student_required, student_owns_record

# student_bp = Blueprint('student', __name__)


# @student_bp.route('/dashboard')
# @login_required
# @student_required
# def dashboard():
#     student = current_user.student_profile
#     return render_template('student/dashboard.html',
#                            title='Student Dashboard', student=student)


# @student_bp.route('/attendance/<int:student_id>')
# @login_required
# @student_required              # Layer 2: must be a student
# @student_owns_record           # Layer 3: must be viewing OWN record
# def view_attendance(student_id):
#     """
#     Student views their own attendance.
#     If student_id in URL doesn't match logged-in student → 403.
#     """
#     from app.models.attendance import Attendance
#     from app.models.subject import Subject
#     student = g.owned_student   # fetched by @student_owns_record
#     records = student.attendance_records.order_by(
#         Attendance.date.desc()
#     ).all()
#     return render_template('student/attendance.html',
#                            student=student, records=records,
#                            title='My Attendance')


# # ══════════════════════════════════════════════════════════════════════
# #  QR ATTENDANCE SCAN
# #  This route is the destination that the QR code points to.
# #
# #  Flow:
# #    1. Teacher generates QR  → encodes URL /student/scan?token=<uuid>
# #    2. Student scans QR on phone
# #    3. Phone opens the URL; if not logged in Flask-Login redirects to
# #       /auth/login?next=/student/scan?token=<uuid>
# #    4. Student logs in → auth.login redirects back here with token intact
# #    5. This route validates the token and records attendance
# # ══════════════════════════════════════════════════════════════════════

# @student_bp.route('/scan')
# @login_required
# @student_required
# def scan_qr():
#     """
#     GET /student/scan?token=<uuid>

#     Validates the QR token and marks the logged-in student as Present
#     for the subject/date linked to that session.

#     No POST needed — the token in the URL is all the data required.
#     This makes it safe to reload the page without re-submitting anything.
#     """
#     from app.services.qr_service import mark_attendance_via_qr

#     token = request.args.get('token', '').strip()

#     if not token:
#         flash('No QR token found. Please scan the QR code again.', 'danger')
#         return redirect(url_for('student.dashboard'))

#     record, qr_session, error = mark_attendance_via_qr(current_user, token)

#     if error:
#         # Token invalid, expired, session closed, or not enrolled
#         return render_template(
#             'student/scan_result.html',
#             success=False,
#             already_marked=False,
#             record=None,
#             qr_session=None,
#             message=error,
#             title='Scan Result',
#         )

#     # record is None when the student was already marked for this session
#     already_marked = (record is None and qr_session is not None)

#     return render_template(
#         'student/scan_result.html',
#         success=True,
#         already_marked=already_marked,
#         record=record,
#         qr_session=qr_session,
#         message=None,
#         title='Attendance Marked' if not already_marked else 'Already Marked',
#     )

"""
STUDENT ROUTES
==============
Students can only read their OWN data.
Three main sections:
  1. Dashboard   — overall summary of subjects + attendance + alerts
  2. Subjects    — enrolled subjects with per-subject attendance
  3. Attendance  — detailed records, semester history
  4. Notifications — inbox, mark read, mark all read, delete
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
    """
    Student home page.
    Shows: overall attendance %, subject cards, recent notifications,
    and any low-attendance warnings.
    """
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
    """
    Dedicated subjects page — lists all enrolled subjects with
    per-subject attendance, teachers, and what-if helpers.
    """
    from app.services.student_service import get_subjects_with_attendance
    student  = current_user.student_profile
    subjects = get_subjects_with_attendance(student) if student else []
    return render_template('student/subjects.html',
                           title='My Subjects',
                           student=student,
                           subjects=subjects)


# ══════════════════════════════════════════════════════════════════════
#  ATTENDANCE
# ══════════════════════════════════════════════════════════════════════

@student_bp.route('/attendance/<int:student_id>')
@login_required
@student_required
@student_owns_record
def view_attendance(student_id):
    """
    Full attendance detail — per-subject breakdown with record-by-record
    history. Supports switching between semesters via query param.
    """
    from app.services.attendance_service import get_student_attendance_summary
    student  = g.owned_student
    semester = request.args.get('semester', type=int, default=student.semester)
    summary  = get_student_attendance_summary(student.id, semester=semester)

    # Build semester options from attendance history
    from app import db
    from app.models.attendance import Attendance
    past_sems = (
        db.session.query(Attendance.semester)
        .filter_by(student_id=student.id)
        .distinct()
        .order_by(Attendance.semester.desc())
        .all()
    )
    semester_options = [r[0] for r in past_sems]

    # Pre-fetch per-subject records so the template doesn't need DB calls
    from app.models.attendance import Attendance as Att
    from collections import defaultdict

    all_records = (
        Att.query
        .filter_by(student_id=student.id, semester=semester)
        .order_by(Att.date.desc())
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
    """
    Full notifications page — shows all notifications with read/unread state.
    Unread notifications are highlighted. Most recent first.
    """
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
    """
    Mark a single notification as read.
    Returns JSON if the request is AJAX, otherwise redirects.
    """
    from app.services.student_service import mark_notification_read as svc_mark
    success, error = svc_mark(current_user, notif_id)

    # AJAX request (called from JavaScript)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if success:
            return jsonify({'ok': True})
        return jsonify({'ok': False, 'error': error}), 400

    # Regular form POST
    if not success:
        flash(error, 'danger')
    return redirect(url_for('student.notifications'))


@student_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
@student_required
def mark_all_read():
    """Mark all unread notifications as read in one action."""
    from app.services.student_service import mark_all_notifications_read
    count = mark_all_notifications_read(current_user)
    if count:
        flash(f'{count} notification(s) marked as read.', 'success')
    else:
        flash('No unread notifications.', 'info')
    return redirect(url_for('student.notifications'))


@student_bp.route('/notifications/<int:notif_id>/delete', methods=['POST'])
@login_required
@student_required
def delete_notification(notif_id):
    """Delete a single read notification."""
    from app.services.student_service import delete_notification as svc_delete
    success, error = svc_delete(current_user, notif_id)
    if not success:
        flash(error, 'danger')
    return redirect(url_for('student.notifications'))


# ══════════════════════════════════════════════════════════════════════
#  QR ATTENDANCE SCAN  (Step 14.5)
#  URL: /scan/<session_id>
#  This route is what the QR code encodes.
#  The student's phone camera opens this URL after scanning.
# ══════════════════════════════════════════════════════════════════════

@student_bp.route('/scan/<session_id>')
@login_required
@student_required
def scan_qr(session_id):
    """
    Called when a student scans a QR code with their phone.

    FLOW:
      1. @login_required  — if not logged in, redirect to login page.
                            Flask-Login saves this URL as 'next' so after
                            login the student is brought straight back here.
      2. @student_required — only students can scan. A teacher accidentally
                             scanning gets a 403, not a duplicate record.
      3. validate_session  — checks the session exists, is active, not expired.
      4. Enrollment check  — student must be in the subject's dept/sem/program.
      5. Duplicate check   — already marked today? Show info, don't double-mark.
      6. mark_attendance   — calls the SAME service used by manual marking.
                             All existing rules apply (duplicate prevention,
                             DB unique constraint, low-att notifications).
      7. increment_scan_count — update the teacher's live counter.
      8. Render result page — success or specific error message.
    """
    from app.services.qr_service import (
        validate_session, increment_scan_count, get_session
    )
    from app.models import Subject, Student, Teacher
    from app.models.user import User
    from app.models.attendance import Attendance
    from app.services.teacher_service import mark_attendance
    from datetime import date

    student = current_user.student_profile

    # ── Step 3: Validate QR session ──────────────────────────────────
    session, error = validate_session(session_id)
    if error:
        return render_template(
            'student/scan_result.html',
            success = False,
            title   = 'QR Scan Failed',
            heading = 'QR Code Invalid',
            message = error,
            icon    = 'x-circle',
            color   = 'danger',
        )

    # ── Step 4: Get subject from session ─────────────────────────────
    subject = Subject.query.get(session['subject_id'])
    if not subject:
        return render_template(
            'student/scan_result.html',
            success = False,
            title   = 'QR Scan Failed',
            heading = 'Subject Not Found',
            message = 'The subject linked to this QR code no longer exists.',
            icon    = 'x-circle',
            color   = 'danger',
        )

    # ── Step 4: Check student is enrolled in this subject ────────────
    # Enrollment is implicit: student's dept + semester + program_type
    # must match the subject's dept + semester + program_type.
    enrolled = (
        student.department_id == subject.department_id and
        student.semester      == subject.semester      and
        student.program_type  == subject.program_type  and
        not student.is_graduated
    )

    if not enrolled:
        return render_template(
            'student/scan_result.html',
            success = False,
            title   = 'Not Enrolled',
            heading = 'You Are Not Enrolled',
            message = (
                f'You are not enrolled in {subject.name} ({subject.code}). '
                f'This QR is for {subject.program_type} Semester {subject.semester} '
                f'students of {subject.department.name}. '
                f'You are currently in Semester {student.semester}.'
            ),
            icon    = 'person-x',
            color   = 'warning',
            subject = subject,
        )

    # ── Step 5: Check for duplicate — already marked today? ──────────
    today = date.today()
    existing = Attendance.query.filter_by(
        student_id = student.id,
        subject_id = subject.id,
        date       = today,
    ).first()

    if existing:
        return render_template(
            'student/scan_result.html',
            success = True,
            title   = 'Already Marked',
            heading = 'Already Marked Present',
            message = (
                f'Your attendance for {subject.name} on '
                f'{today.strftime("%d %b %Y")} has already been recorded as '
                f'<strong>{existing.status.upper()}</strong>. '
                f'No duplicate entry was created.'
            ),
            icon    = 'check-circle',
            color   = 'info',
            subject = subject,
            student = student,
        )

    # ── Step 6: Get the teacher who owns this session ─────────────────
    # mark_attendance() needs a teacher_user (User object, not Teacher).
    # The session stores teacher_id (Teacher.id), so we look up their User.
    teacher_profile = Teacher.query.get(session['teacher_id'])
    if not teacher_profile:
        return render_template(
            'student/scan_result.html',
            success = False,
            title   = 'QR Scan Failed',
            heading = 'Session Error',
            message = 'Could not find the teacher for this QR session. Please ask your teacher to generate a new QR code.',
            icon    = 'x-circle',
            color   = 'danger',
        )

    teacher_user = teacher_profile.user

    # ── Step 7: Mark attendance via existing service ──────────────────
    # status_map = {student_id: 'present'} — one student, present status.
    # This calls the SAME mark_attendance() used by manual form marking.
    # All rules apply: duplicate check, DB constraint, low-att alerts.
    result = mark_attendance(
        teacher_user = teacher_user,
        subject_id   = subject.id,
        status_map   = {student.id: 'present'},
        mark_date    = today,
    )

    if 'error' in result:
        # mark_attendance returned an error (e.g. already marked by teacher)
        return render_template(
            'student/scan_result.html',
            success = False,
            title   = 'Could Not Mark',
            heading = 'Attendance Not Marked',
            message = result['error'],
            icon    = 'exclamation-circle',
            color   = 'warning',
            subject = subject,
        )

    # ── Step 8: Increment teacher's scan counter ──────────────────────
    increment_scan_count(session_id)

    # ── Step 9: Show success ──────────────────────────────────────────
    return render_template(
        'student/scan_result.html',
        success = True,
        title   = 'Attendance Marked',
        heading = 'Attendance Marked ✓',
        message = (
            f'You have been marked <strong>PRESENT</strong> for '
            f'<strong>{subject.name}</strong> ({subject.code}) '
            f'on {today.strftime("%A, %d %b %Y")}.'
        ),
        icon    = 'check-circle-fill',
        color   = 'success',
        subject = subject,
        student = student,
    )