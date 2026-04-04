"""
STUDENT ROUTES
==============
Students can only view their OWN data.
@student_owns_record prevents any student from viewing another's records.
"""

from flask import Blueprint, render_template, g
from flask_login import login_required, current_user
from app.decorators import student_required, student_owns_record

student_bp = Blueprint('student', __name__)


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    student = current_user.student_profile
    return render_template('student/dashboard.html',
                           title='Student Dashboard', student=student)


@student_bp.route('/attendance/<int:student_id>')
@login_required
@student_required              # Layer 2: must be a student
@student_owns_record           # Layer 3: must be viewing OWN record
def view_attendance(student_id):
    """
    Student views their own attendance.
    If student_id in URL doesn't match logged-in student → 403.
    """
    from app.models.attendance import Attendance
    from app.models.subject import Subject
    student  = g.owned_student   # fetched by @student_owns_record
    records  = student.attendance_records.order_by(
        Attendance.date.desc()
    ).all()
    return render_template('student/attendance.html',
                           student=student, records=records,
                           title='My Attendance')