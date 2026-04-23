"""
STUDENT ROUTES
==============
Students can only view their OWN data.
@student_owns_record prevents any student from viewing another's records.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, g
from flask_login import login_required, current_user
from app.decorators import student_required, student_owns_record

student_bp = Blueprint('student', __name__)


# ── original routes (unchanged) ──────────────────────────────────────

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    student = current_user.student_profile
    return render_template('student/dashboard.html',
                           title='Student Dashboard', student=student)


@student_bp.route('/attendance/<int:student_id>')
@login_required
@student_required
@student_owns_record
def view_attendance(student_id):
    from app.models.attendance import Attendance
    student = g.owned_student
    records = student.attendance_records.order_by(
        Attendance.date.desc()
    ).all()
    return render_template('student/attendance.html',
                           student=student, records=records,
                           title='My Attendance')


# ── QR attendance scan ────────────────────────────────────────────────
#
# GET  /student/scan?token=<signed>
#   → decode token, show a form with subject info + roll number field
#
# POST /student/scan?token=<signed>
#   → verify roll number matches logged-in student
#   → insert Attendance row (marked_by_id = teacher who generated QR)
#   → show result page
#
# The token is a signed payload created by itsdangerous (bundled with
# Flask) containing: subject_id, teacher_id, date, expires_at.
# It is generated fresh each time a teacher clicks Generate QR, so
# each QR code is unique and time-limited.
# ─────────────────────────────────────────────────────────────────────

@student_bp.route('/scan', methods=['GET', 'POST'])
@login_required
@student_required
def scan_qr():
    from datetime import date, datetime, timezone
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
    from flask import current_app
    from app import db
    from app.models.attendance import Attendance
    from app.models.subject    import Subject
    from app.models.teacher    import Teacher

    token = request.args.get('token', '').strip()

    def show_error(msg):
        return render_template('student/scan_qr.html',
                               error=msg,
                               subject=None,
                               token=token,
                               title='Attendance — Error')

    # 1. Token must be present
    if not token:
        return show_error('No QR token found. Please scan the QR code again.')

    # 2. Verify signature — rejects forged or tampered tokens
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        payload = s.loads(token, max_age=3600)  # hard ceiling: 1 hour
    except SignatureExpired:
        return show_error(
            'This QR code has expired. Ask your teacher to generate a new one.')
    except BadSignature:
        return show_error(
            'Invalid QR code. Please scan the code shown by your teacher.')

    # 3. Check the teacher's chosen expiry window (e.g. 15 min)
    expires_at = payload.get('expires_at', 0)
    if datetime.now(timezone.utc).timestamp() > expires_at:
        return show_error(
            'This QR session has closed. Ask your teacher to generate a new one.')

    # 4. Load subject and teacher from the token payload
    subject = Subject.query.get(payload.get('subject_id'))
    teacher = Teacher.query.get(payload.get('teacher_id'))
    if not subject or not teacher:
        return show_error(
            'QR code references an unknown subject. Contact your teacher.')

    attendance_date = date.fromisoformat(payload['date'])
    student = current_user.student_profile

    # 5. Make sure this student is enrolled in the subject
    enrolled = (
        subject.department_id == student.department_id and
        subject.semester      == student.semester      and
        subject.program_type  == student.program_type  and
        subject.is_active
    )
    if not enrolled:
        return show_error(
            f'You are not enrolled in {subject.name} ({subject.code}). '
            'Contact your HOD if this is incorrect.')

    # 6. Already marked?
    existing = Attendance.query.filter_by(
        student_id=student.id,
        subject_id=subject.id,
        date=attendance_date,
    ).first()

    # ── GET — show the confirmation form ─────────────────────────────
    if request.method == 'GET':
        return render_template(
            'student/scan_qr.html',
            error=None,
            subject=subject,
            teacher=teacher,
            attendance_date=attendance_date,
            already_marked=(existing is not None),
            student=student,
            token=token,
            title=f'Mark Attendance — {subject.code}',
        )

    # ── POST — student submitted the form ────────────────────────────
    entered_roll = request.form.get('roll_number', '').strip().upper()

    # Validate: roll number must match the logged-in student's record
    if entered_roll != student.roll_number.upper():
        flash('Roll number does not match your account. Please check and try again.', 'danger')
        return render_template(
            'student/scan_qr.html',
            error=None,
            subject=subject,
            teacher=teacher,
            attendance_date=attendance_date,
            already_marked=(existing is not None),
            student=student,
            token=token,
            title=f'Mark Attendance — {subject.code}',
        )

    # Already marked — show info, no duplicate insert
    if existing:
        return render_template(
            'student/scan_result.html',
            already_marked=True,
            subject=subject,
            attendance_date=attendance_date,
            title='Already Recorded',
        )

    # Insert the attendance row.
    # marked_by_id = teacher.id because the DB constraint requires a teacher FK.
    # The teacher is the one who authorised the session by generating the QR.
    db.session.add(Attendance(
        student_id   = student.id,
        subject_id   = subject.id,
        marked_by_id = teacher.id,
        date         = attendance_date,
        status       = 'present',
        semester     = student.semester,
    ))
    db.session.commit()

    return render_template(
        'student/scan_result.html',
        already_marked=False,
        subject=subject,
        attendance_date=attendance_date,
        title='Attendance Marked ✅',
    )