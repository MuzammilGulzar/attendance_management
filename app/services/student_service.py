"""
STUDENT SERVICE
===============
Business logic for the student dashboard.

Covers:
  1. Subject listing — what subjects is this student enrolled in
  2. Notification management — fetch, mark read, create alerts
  3. Low-attendance detection — auto-generate warning notifications
  4. Dashboard data assembly — one call that packages everything

Design principle:
  The student can only READ — they cannot create, edit, or delete
  any academic data. This service only contains query functions
  and notification helpers.
"""

from datetime import datetime
from app import db
from app.models.student       import Student
from app.models.subject       import Subject
from app.models.notification  import Notification
from app.models.attendance    import Attendance
from app.models.user          import User


# ══════════════════════════════════════════════════════════════════════
#  SUBJECTS
# ══════════════════════════════════════════════════════════════════════

def get_enrolled_subjects(student):
    """
    Return all active subjects this student is enrolled in.

    Enrollment is implicit — a student is in all subjects that match:
      department_id == student.department_id
      semester      == student.semester
      program_type  == student.program_type
      is_active     == True

    Returns a list of Subject objects ordered by semester then name.
    """
    return (
        Subject.query
        .filter_by(
            department_id = student.department_id,
            semester      = student.semester,
            program_type  = student.program_type,
            is_active     = True,
        )
        .order_by(Subject.name)
        .all()
    )


def get_subjects_with_attendance(student):
    """
    Return subjects with pre-computed attendance stats per subject.
    Used for the subjects page — shows both subject info and % together.

    Returns a list of dicts:
      subject         → Subject object
      pct             → float attendance percentage
      present         → int
      absent          → int
      leave           → int
      event           → int
      conducted       → int
      status          → 'ok' | 'warning' | 'low' | 'no_data'
      classes_needed  → how many more classes needed to reach 75%
      teachers        → list of teacher names for this subject
      last_marked     → date of most recent attendance record (or None)
    """
    from app.services.attendance_service import (
        calculate_percentage,
        calculate_required_classes,
        THRESHOLD_LOW, THRESHOLD_WARNING
    )

    subjects   = get_enrolled_subjects(student)
    result     = []

    for subj in subjects:
        # Fetch all attendance records for this student in this subject
        records = (
            Attendance.query
            .filter_by(student_id=student.id, subject_id=subj.id)
            .order_by(Attendance.date.desc())
            .all()
        )

        stats             = calculate_percentage(records)
        stats['subject']  = subj
        stats['classes_needed'] = calculate_required_classes(
            stats['pct'], stats['conducted']
        )

        # Teachers assigned to this subject
        teachers = subj.teachers.all()
        stats['teachers'] = [t.full_name for t in teachers] if teachers else []

        # Date of most recent attendance marking
        stats['last_marked'] = records[0].date if records else None

        result.append(stats)

    return result


# ══════════════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ══════════════════════════════════════════════════════════════════════

def get_notifications(user, unread_only=False, limit=50):
    """
    Fetch notifications for a user.

    unread_only: if True, return only unread notifications.
    limit: maximum number to return (most recent first).

    Returns a list of Notification objects.
    """
    q = user.notifications
    if unread_only:
        q = q.filter_by(is_read=False)
    return q.limit(limit).all()


def get_unread_count(user):
    """
    Quick count of unread notifications.
    Used for the navbar bell badge — called on every page load.
    Kept as a separate lightweight function to avoid fetching full objects.
    """
    return user.notifications.filter_by(is_read=False).count()


def mark_notification_read(user, notification_id):
    """
    Mark a single notification as read.
    Verifies the notification belongs to this user before marking.

    Returns: (True, None) on success
             (False, error_msg) on failure
    """
    notif = Notification.query.get(notification_id)
    if not notif:
        return False, 'Notification not found.'
    if notif.user_id != user.id:
        return False, 'You do not have access to this notification.'
    if notif.is_read:
        return True, None    # already read — no-op, not an error

    notif.mark_as_read()
    db.session.commit()
    return True, None


def mark_all_notifications_read(user):
    """
    Mark ALL unread notifications for this user as read in one query.
    More efficient than looping one at a time.

    Returns: int — number of notifications marked.
    """
    unread = user.notifications.filter_by(is_read=False).all()
    now    = datetime.utcnow()
    count  = 0
    for n in unread:
        n.is_read = True
        n.read_at = now
        count += 1
    if count:
        db.session.commit()
    return count


def delete_notification(user, notification_id):
    """
    Delete a single read notification.
    Unread notifications cannot be deleted — they must be read first.

    Returns: (True, None) | (False, error_msg)
    """
    notif = Notification.query.get(notification_id)
    if not notif:
        return False, 'Notification not found.'
    if notif.user_id != user.id:
        return False, 'You do not have access to this notification.'
    if not notif.is_read:
        return False, 'Mark the notification as read before deleting.'

    db.session.delete(notif)
    db.session.commit()
    return True, None


# ══════════════════════════════════════════════════════════════════════
#  LOW-ATTENDANCE AUTO-ALERTS
#  Called after each attendance marking session to notify students
#  whose percentage has dropped below the threshold.
# ══════════════════════════════════════════════════════════════════════

def check_and_notify_low_attendance(student_id):
    """
    Check this student's attendance across all subjects.
    Send a notification if any subject drops below 75% AND no
    similar unread warning already exists for that subject.

    This prevents spamming the student with the same alert every day.

    Called by: teacher_service.mark_attendance() after each session.
    Can also be called on a scheduler for daily updates.

    Returns: int — number of new notifications sent.
    """
    from app.services.attendance_service import (
        calculate_percentage, THRESHOLD_LOW
    )

    student  = Student.query.get(student_id)
    if not student or not student.user.is_active:
        return 0

    subjects = get_enrolled_subjects(student)
    sent     = 0

    for subj in subjects:
        records   = Attendance.query.filter_by(
            student_id=student.id, subject_id=subj.id
        ).all()
        stats     = calculate_percentage(records)

        # Only alert if below threshold AND has actual data
        if stats['conducted'] == 0 or stats['pct'] >= THRESHOLD_LOW:
            continue

        # Check: does an unread low-attendance notification already exist
        # for this specific subject? Don't spam.
        already_notified = Notification.query.filter_by(
            user_id = student.user_id,
            is_read = False,
        ).filter(
            Notification.title.contains(subj.code)
        ).first()

        if already_notified:
            continue    # unread warning already exists — skip

        # Create the warning notification
        pct_display = stats['pct']
        classes_short = max(0, int(
            (THRESHOLD_LOW / 100 * stats['conducted'] - stats['present'])
            / (1 - THRESHOLD_LOW / 100)
        ) + 1) if stats['pct'] < THRESHOLD_LOW else 0

        db.session.add(Notification(
            user_id = student.user_id,
            type    = 'danger' if stats['pct'] < 60 else 'warning',
            title   = f'Low Attendance Alert — {subj.code}',
            message = (
                f'Your attendance in {subj.name} ({subj.code}) has dropped to '
                f'{pct_display}% (Semester {student.semester}). '
                f'Minimum required is 75%. '
                f'You need to attend at least {classes_short} more consecutive '
                f'class(es) to reach the threshold. '
                f'Contact your teacher or HOD if you have an authorised absence.'
            )
        ))
        sent += 1

    if sent:
        db.session.commit()
    return sent


# ══════════════════════════════════════════════════════════════════════
#  DASHBOARD DATA ASSEMBLER
#  One call that builds everything the student dashboard needs.
# ══════════════════════════════════════════════════════════════════════

def get_student_dashboard_data(student):
    """
    Assembles all data for the student dashboard in one call.

    Returns a dict with:
      student           → Student object
      subjects          → list of subject-with-attendance dicts
      overall_summary   → overall attendance stats across all subjects
      notifications     → 10 most recent notifications (read + unread)
      unread_count      → int
      low_att_subjects  → subjects where pct < 75%
      semester_history  → list of past semesters for the dropdown
    """
    from app.services.attendance_service import (
        calculate_percentage, calculate_required_classes
    )

    subjects_with_att = get_subjects_with_attendance(student)

    # Overall: combine all records from all current-semester subjects
    all_records = (
        Attendance.query
        .filter_by(student_id=student.id, semester=student.semester)
        .all()
    )
    overall = calculate_percentage(all_records)
    overall['classes_needed'] = calculate_required_classes(
        overall['pct'], overall['conducted']
    )

    # Subjects with attendance below threshold
    low_att_subjects = [
        s for s in subjects_with_att
        if s['status'] == 'low' and s['conducted'] > 0
    ]

    # Recent notifications (first 10 — full list on notifications page)
    notifications = get_notifications(student.user, limit=10)
    unread_count  = get_unread_count(student.user)

    # Past semesters this student has attendance data for
    past_sems = (
        db.session.query(Attendance.semester)
        .filter_by(student_id=student.id)
        .distinct()
        .order_by(Attendance.semester.desc())
        .all()
    )
    semester_history = [r[0] for r in past_sems]

    return {
        'student'          : student,
        'subjects'         : subjects_with_att,
        'overall'          : overall,
        'notifications'    : notifications,
        'unread_count'     : unread_count,
        'low_att_subjects' : low_att_subjects,
        'semester_history' : semester_history,
    }
