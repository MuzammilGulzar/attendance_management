"""
TEACHER ROUTES
==============
Teachers can view their subjects, mark attendance, and see history.
They CANNOT edit any existing record — that is HOD-only.
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


@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    data = get_teacher_dashboard_data(current_user)
    return render_template('teacher/dashboard.html',
                           title='Teacher Dashboard', data=data)


@teacher_bp.route('/subject/<int:subject_id>/students')
@login_required
@teacher_required
@teacher_owns_subject
def subject_students(subject_id):
    subject = g.owned_subject
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


@teacher_bp.route('/attendance/mark/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
@teacher_owns_subject
def mark_attendance_view(subject_id):
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
            teacher_user=current_user,
            subject_id=subject_id,
            status_map=status_map,
            mark_date=mark_date,
        )
        if 'error' in result:
            flash(result['error'], 'danger')
        else:
            flash(result['message'], 'success')
            return redirect(url_for('teacher.dashboard'))

    session_data, error = get_attendance_session(
        teacher_user=current_user,
        subject_id=subject_id,
        for_date=mark_date,
    )
    if error:
        flash(error, 'danger')
        return redirect(url_for('teacher.dashboard'))
    return render_template('teacher/mark_attendance.html',
                           session=session_data,
                           subject=subject,
                           mark_date=mark_date,
                           title=f'Attendance — {subject.code}')


@teacher_bp.route('/attendance/history/<int:subject_id>')
@login_required
@teacher_required
@teacher_owns_subject
def attendance_history(subject_id):
    subject = g.owned_subject
    history = get_subject_attendance_history(current_user, subject_id)
    return render_template('teacher/attendance_history.html',
                           subject=subject,
                           history=history,
                           status_colors=STATUS_COLORS,
                           status_labels=STATUS_LABELS,
                           title=f'{subject.code} — History')


@teacher_bp.route('/attendance/student/<int:subject_id>/<int:student_id>')
@login_required
@teacher_required
@teacher_owns_subject
def student_attendance_detail(subject_id, student_id):
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


@teacher_bp.route('/notifications')
@login_required
@teacher_required
def notifications_inbox():
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
    from app.services.notification_service import mark_all_read
    count = mark_all_read(current_user)
    flash(f'{count} notification(s) marked as read.' if count
          else 'All notifications are already read.',
          'success' if count else 'info')
    return redirect(url_for('teacher.notifications_inbox'))


# ══════════════════════════════════════════════════════════════════════
#  QR ATTENDANCE  — NEW ROUTES ONLY, everything above is untouched
# ══════════════════════════════════════════════════════════════════════

@teacher_bp.route('/qr/generate/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
@teacher_owns_subject
def generate_qr(subject_id):
    """
    GET  → show expiry-duration picker
    POST → create signed token + QR PNG, display for class to scan

    The QR encodes a URL:  /student/scan?token=<signed_payload>
    The payload contains: subject_id, teacher_id, date, expires_at.
    Signed with app SECRET_KEY via itsdangerous — cannot be forged.
    Each generation produces a unique token, so every QR is different.
    """
    import os, uuid
    from datetime import datetime, timezone, timedelta
    from itsdangerous import URLSafeTimedSerializer
    from flask import current_app

    subject = g.owned_subject
    teacher = current_user.teacher_profile

    if request.method == 'GET':
        return render_template('teacher/qr_generate.html',
                               subject=subject,
                               title=f'Generate QR — {subject.code}')

    # Build signed token
    try:
        expiry_minutes = max(5, min(int(request.form.get('expiry_minutes', 15)), 60))
    except (TypeError, ValueError):
        expiry_minutes = 15

    now        = datetime.now(timezone.utc)
    expires_at = (now + timedelta(minutes=expiry_minutes)).timestamp()

    s     = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = s.dumps({
        'subject_id': subject.id,
        'teacher_id': teacher.id,
        'date'      : date.today().isoformat(),
        'expires_at': expires_at,
    })

    base_url = request.host_url.rstrip('/')
    scan_url = f'{base_url}/student/scan?token={token}'

    # Generate QR PNG using OpenCV (already installed on the server)
    qr_image_url = _generate_qr_png(scan_url, current_app)

    return render_template('teacher/qr_attendance.html',
                           subject=subject,
                           scan_url=scan_url,
                           qr_image_url=qr_image_url,
                           expiry_minutes=expiry_minutes,
                           expires_at=now + timedelta(minutes=expiry_minutes),
                           title=f'QR Attendance — {subject.code}')


def _generate_qr_png(scan_url, app):
    """
    Generate a QR code PNG from scan_url and save to app/static/qr/.
    Uses OpenCV which is already installed. Falls back to None so the
    template can show the raw URL instead.
    """
    import os, uuid
    try:
        import cv2
        import numpy as np

        qr      = cv2.QRCodeEncoder.create()
        matrix  = qr.encode(scan_url)   # shape (H, W), values 0/255

        # Scale up each module to 10×10 pixels for easy scanning
        scale = 10
        big   = np.repeat(np.repeat(matrix, scale, axis=0), scale, axis=1)

        # Add a white border (4 modules = 40px) so scanners work at edges
        border = 40
        h, w   = big.shape
        canvas = np.full((h + border*2, w + border*2), 255, dtype=np.uint8)
        canvas[border:border+h, border:border+w] = big

        # Save
        qr_dir = os.path.join(app.root_path, 'static', 'qr')
        os.makedirs(qr_dir, exist_ok=True)
        img_name = f'{uuid.uuid4()}.png'
        cv2.imwrite(os.path.join(qr_dir, img_name), canvas)

        from flask import url_for
        return url_for('static', filename=f'qr/{img_name}')

    except Exception:
        return None   # template will show raw URL as fallback