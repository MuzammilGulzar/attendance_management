"""
QR SERVICE
==========
Handles creation and validation of QR code attendance sessions.

HOW IT FITS INTO THE EXISTING SYSTEM
──────────────────────────────────────
The existing mark_attendance() in teacher_service.py is the
single source of truth for writing attendance records. This service
does NOT replace or duplicate that logic. It only:

  1. Creates a short-lived session that authorises ONE class
  2. Validates whether that session is still alive
  3. Provides a roll-number-based path to mark attendance
     without requiring the student to be logged in

STORAGE CHOICE: IN-MEMORY DICTIONARY
──────────────────────────────────────
Sessions are stored in a plain Python dict called _sessions.
This is intentional at this stage because:

  • QR sessions are TEMPORARY — they live for 5 minutes only.
    Storing them in the database would mean constantly inserting
    and then querying rows that become useless immediately.
  • Simplicity — no migration, no new table, no ORM query needed
    to create or look up a session.
  • Speed — dict lookup is O(1). No DB round-trip on every scan.

TRADE-OFF:
  In-memory storage is lost if the server restarts.
  For a production multi-server setup, move to Redis —
  the interface stays the same, only the storage backend changes.

UPDATED FLOW (Step A redesign):
  Teacher generates QR → session created here
  Student scans QR    → lands on public form (NO login required)
  Student types roll number + name
  mark_by_roll_number() verifies and marks attendance
"""

import uuid
import os
import qrcode
from datetime import datetime, timedelta


# ══════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════

QR_EXPIRY_MINUTES = 5
# How long a QR code stays valid after generation.

_SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
_APP_DIR     = os.path.dirname(_SERVICE_DIR)
QR_FOLDER    = os.path.join(_APP_DIR, 'static', 'qr')

QR_BASE_URL = os.environ.get('QR_BASE_URL', 'http://localhost:5000')


# ══════════════════════════════════════════════════════════════════════
#  IN-MEMORY SESSION STORE
#
#  Structure of each entry:
#  {
#    "session_id"  : "f47ac10b-...",   UUID string
#    "subject_id"  : 3,                Subject.id
#    "teacher_id"  : 7,                Teacher.id (not User.id)
#    "created_at"  : datetime,         when created
#    "expires_at"  : datetime,         created_at + 5 minutes
#    "is_active"   : True/False,       False = cancelled or expired
#    "scan_count"  : 0,                successful scans so far
#    "image_path"  : "qr/<uuid>.png"   relative path for url_for('static')
#  }
# ══════════════════════════════════════════════════════════════════════

_sessions = {}


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 1: create_session
# ══════════════════════════════════════════════════════════════════════

def create_session(teacher_id: int, subject_id: int) -> dict:
    """
    Create a new QR attendance session for a class.

    Called when a teacher clicks "Generate QR" on the teacher dashboard.

    Steps:
      1. Generate a UUID4 (random, unguessable 36-char string)
      2. Calculate expires_at = now + 5 minutes
      3. Generate the QR PNG image (saved to app/static/qr/)
      4. Store everything in _sessions dict
      5. Return the full session dict to the route

    Parameters:
      teacher_id — Teacher.id (NOT User.id) of the generating teacher
      subject_id — Subject.id this QR session is for

    Returns:
      Dict with all session fields including image_path
    """
    # Always sweep expired sessions before creating a new one.
    # This keeps the dict from growing indefinitely.
    cleanup_expired_sessions()

    session_id = str(uuid.uuid4())
    now        = datetime.utcnow()
    expires_at = now + timedelta(minutes=QR_EXPIRY_MINUTES)
    image_path = generate_qr_image(session_id)

    session = {
        'session_id' : session_id,
        'subject_id' : subject_id,
        'teacher_id' : teacher_id,
        'created_at' : now,
        'expires_at' : expires_at,
        'is_active'  : True,
        'scan_count' : 0,
        'image_path' : image_path,
    }

    _sessions[session_id] = session
    return session


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 2: validate_session
# ══════════════════════════════════════════════════════════════════════

def validate_session(session_id: str) -> tuple:
    """
    Check whether a QR session is still valid.

    Called when a student's browser hits /scan/<session_id>.

    Three checks in order:
      1. Does the session exist?         → not found error
      2. Has the teacher cancelled it?   → cancelled error
      3. Has the 5-minute window passed? → expired error

    Returns:
      (session_dict, None)        on success
      (None, error_message_str)   on any failure
    """
    session = _sessions.get(session_id)

    if session is None:
        return None, (
            'QR code not found. '
            'It may have expired or the server was restarted. '
            'Please ask your teacher to generate a new QR code.'
        )

    if not session['is_active']:
        return None, 'This QR session has been cancelled by the teacher.'

    now = datetime.utcnow()
    if session['expires_at'] <= now:
        _sessions[session_id]['is_active'] = False
        minutes_ago = int((now - session['expires_at']).total_seconds() / 60)
        ago_text    = f'{minutes_ago} minute(s) ago' if minutes_ago > 0 else 'just now'
        return None, (
            f'QR code expired {ago_text}. '
            f'QR codes are only valid for {QR_EXPIRY_MINUTES} minutes. '
            f'Please ask your teacher to generate a new one.'
        )

    return session, None


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 3: get_session_public_info
#  NEW — used by the public scan form page
# ══════════════════════════════════════════════════════════════════════

def get_session_public_info(session_id: str) -> dict | None:
    """
    Return only the safe, public information about a session.

    This is called by the GET /scan/<session_id> route to populate
    the attendance form shown to the student.

    WHY a separate function instead of exposing get_session() directly?
    ────────────────────────────────────────────────────────────────────
    get_session() returns the raw internal dict including teacher_id,
    image_path, and other internals that the student-facing page does
    not need and should not see.

    This function returns only what the form page needs:
      - subject name and code (so the student can confirm it's correct)
      - time_remaining (so the student can see the countdown)
      - session_id (needed for the form POST action)
      - is_valid (False means expired/cancelled — form should not show)

    The subject object is fetched here by DB lookup so the route
    doesn't need to duplicate that query.

    Parameters:
      session_id — UUID string from the URL

    Returns:
      None — if session doesn't exist in memory
      dict — {
        'session_id'    : str,
        'is_valid'      : bool,     False if expired or cancelled
        'error'         : str|None, reason if not valid
        'subject_id'    : int,
        'time_remaining': int,      seconds left (0 if expired)
        'expires_at'    : datetime,
      }
    """
    session = _sessions.get(session_id)
    if session is None:
        return None

    # Check validity (reuse validate_session logic)
    valid_sess, error = validate_session(session_id)

    return {
        'session_id'    : session_id,
        'is_valid'      : valid_sess is not None,
        'error'         : error,
        'subject_id'    : session['subject_id'],
        'time_remaining': get_time_remaining(session_id),
        'expires_at'    : session['expires_at'],
    }


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 4: mark_by_roll_number
#  NEW — the core of the redesigned scan flow
# ══════════════════════════════════════════════════════════════════════

def mark_by_roll_number(session_id: str, roll_number: str, full_name: str) -> tuple:
    """
    Mark attendance for a student identified by roll number.

    This is the core function of the new public QR flow.
    No login required — the student just types their roll number.

    Called by: POST /scan/<session_id>

    VALIDATION STEPS (in order — first failure stops the chain):
    ─────────────────────────────────────────────────────────────
    1. Validate session        — still alive? (not expired/cancelled)
    2. Clean roll_number input — strip whitespace, uppercase
    3. Find student in DB      — does this roll number exist?
    4. Check not graduated     — graduated students can't attend
    5. Check enrollment        — student's dept+semester+program
                                 must match the subject's
    6. Check duplicate         — already marked today for this subject?
    7. Get teacher user        — needed by mark_attendance() service
    8. Call mark_attendance()  — the existing service (single source of truth)
    9. Increment scan_count    — update teacher's live counter

    Name verification:
    ──────────────────
    The full_name field is NOT used for identity verification.
    A student could type any name and it would still work.
    The name is shown in the confirmation page only — so the
    student can confirm they marked the right person.

    This is intentional: roll numbers are the authoritative identity
    in an academic system. Names can be spelled differently or
    abbreviated. Only the roll number must match exactly.

    Parameters:
      session_id  — UUID string from the form action URL
      roll_number — student-entered roll number (will be uppercased + stripped)
      full_name   — student-entered name (display only, not verified)

    Returns:
      (True,  success_dict)   — attendance marked successfully
      (False, error_str)      — any step failed

    success_dict contains:
      {
        'student_name' : str,   actual name from DB
        'roll_number'  : str,   roll number from DB
        'subject_name' : str,
        'subject_code' : str,
        'date'         : date,
      }
    """
    from app.models.student    import Student
    from app.models.subject    import Subject
    from app.models.teacher    import Teacher
    from app.models.attendance import Attendance
    from app.services.teacher_service import mark_attendance
    from datetime import date

    # ── Step 1: Validate the session ────────────────────────────────
    session, error = validate_session(session_id)
    if error:
        return False, error

    # ── Step 2: Clean the roll number ───────────────────────────────
    # Strip surrounding whitespace and convert to uppercase so that
    # "it2022001", "IT2022001 ", and "IT2022001" all match the same row.
    roll_number = roll_number.strip().upper()

    if not roll_number:
        return False, 'Please enter your roll number.'

    # ── Step 3: Find student by roll number ─────────────────────────
    student = Student.query.filter_by(roll_number=roll_number).first()

    if student is None:
        return False, (
            f'Roll number "{roll_number}" was not found in the system. '
            f'Please check your roll number and try again.'
        )

    # ── Step 4: Check student is not graduated ──────────────────────
    if student.is_graduated:
        return False, (
            f'Roll number "{roll_number}" belongs to a graduated student. '
            f'Graduated students cannot mark attendance.'
        )

    # ── Step 5: Check enrollment in this subject ─────────────────────
    # Enrollment is implicit: student must match the subject's
    # department, semester, and program_type.
    subject = Subject.query.get(session['subject_id'])
    if not subject:
        return False, 'Subject not found. Please ask your teacher to generate a new QR.'

    enrolled = (
        student.department_id == subject.department_id and
        student.semester      == subject.semester      and
        student.program_type  == subject.program_type
    )

    if not enrolled:
        return False, (
            f'Roll number "{roll_number}" is not enrolled in '
            f'{subject.name} ({subject.code}). '
            f'This QR is for {subject.program_type} Semester {subject.semester} '
            f'of {subject.department.name}. '
            f'You are in Semester {student.semester}.'
        )

    # ── Step 6: Check for duplicate attendance today ─────────────────
    today    = date.today()
    existing = Attendance.query.filter_by(
        student_id = student.id,
        subject_id = subject.id,
        date       = today,
    ).first()

    if existing:
        # Already marked — return success so the student sees a
        # friendly confirmation rather than an error.
        return True, {
            'already_marked': True,
            'status'        : existing.status,
            'student_name'  : student.full_name,
            'roll_number'   : student.roll_number,
            'subject_name'  : subject.name,
            'subject_code'  : subject.code,
            'date'          : today,
        }

    # ── Step 7: Get the teacher's User object ────────────────────────
    # mark_attendance() expects a User object (not Teacher.id).
    # The session stores Teacher.id, so we fetch from DB.
    teacher = Teacher.query.get(session['teacher_id'])
    if not teacher:
        return False, (
            'Could not identify the teacher for this session. '
            'Please ask your teacher to regenerate the QR code.'
        )

    # ── Step 8: Mark attendance via existing service ─────────────────
    # We call the SAME mark_attendance() function that the manual
    # attendance form uses. This ensures:
    #   • Duplicate prevention (DB UniqueConstraint + service check)
    #   • Low-attendance notifications are triggered
    #   • total_classes counter on subject is updated
    #   • All business rules apply consistently
    result = mark_attendance(
        teacher_user = teacher.user,
        subject_id   = subject.id,
        status_map   = {student.id: 'present'},
        mark_date    = today,
    )

    if 'error' in result:
        return False, result['error']

    # ── Step 9: Increment teacher's scan counter ──────────────────────
    # Only increment on a fresh successful mark — not on duplicates
    # (duplicates return early above before reaching this point).
    increment_scan_count(session_id)

    return True, {
        'already_marked': False,
        'student_name'  : student.full_name,
        'roll_number'   : student.roll_number,
        'subject_name'  : subject.name,
        'subject_code'  : subject.code,
        'date'          : today,
    }


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 5: deactivate_session
# ══════════════════════════════════════════════════════════════════════

def deactivate_session(session_id: str) -> bool:
    """
    Teacher manually cancels a QR session before it expires.

    Sets is_active = False. Any student who tries to scan after
    this gets a "session cancelled" error.

    Returns True if found and deactivated, False if not found.
    """
    session = _sessions.get(session_id)
    if session is None:
        return False
    _sessions[session_id]['is_active'] = False
    return True


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 6: increment_scan_count
# ══════════════════════════════════════════════════════════════════════

def increment_scan_count(session_id: str):
    """
    Increment scan_count after a student successfully marks attendance.

    Called only on fresh successful marks (not duplicates).
    The teacher's QR display page polls this to show:
    "14 students scanned"
    """
    if session_id in _sessions:
        _sessions[session_id]['scan_count'] += 1


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 7: get_session
# ══════════════════════════════════════════════════════════════════════

def get_session(session_id: str) -> dict | None:
    """
    Retrieve the raw session dict by ID without any validation.

    Used by:
      - Teacher's QR status AJAX endpoint (reads scan_count)
      - cancel_qr route (verifies session belongs to this teacher)

    Returns None if the session doesn't exist.
    """
    return _sessions.get(session_id)


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 8: get_time_remaining
# ══════════════════════════════════════════════════════════════════════

def get_time_remaining(session_id: str) -> int:
    """
    Return seconds remaining until QR expiry.

    Returns 0 if expired or not found.
    Used by:
      - Teacher's QR countdown timer
      - Public scan form countdown (shows student the urgency)
    """
    session = _sessions.get(session_id)
    if session is None:
        return 0
    remaining = (session['expires_at'] - datetime.utcnow()).total_seconds()
    return max(0, int(remaining))


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 9: generate_qr_image
# ══════════════════════════════════════════════════════════════════════

def generate_qr_image(session_id: str) -> str:
    """
    Generate a QR PNG and save it to app/static/qr/<session_id>.png

    The QR encodes: <QR_BASE_URL>/scan/<session_id>
    Example:        http://localhost:5000/scan/f47ac10b-...

    Returns the relative static path: 'qr/<session_id>.png'
    Used in templates as: url_for('static', filename=image_path)
    """
    os.makedirs(QR_FOLDER, exist_ok=True)

    scan_url = f'{QR_BASE_URL}/scan/{session_id}'

    qr = qrcode.QRCode(
        version          = None,
        error_correction = qrcode.constants.ERROR_CORRECT_M,
        box_size         = 10,
        border           = 4,
    )
    qr.add_data(scan_url)
    qr.make(fit=True)

    img         = qr.make_image(fill_color='black', back_color='white')
    filename    = f'{session_id}.png'
    full_path   = os.path.join(QR_FOLDER, filename)
    static_path = f'qr/{filename}'

    img.save(full_path)
    return static_path


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 10: delete_qr_image
# ══════════════════════════════════════════════════════════════════════

def delete_qr_image(session_id: str) -> bool:
    """
    Delete the QR PNG file when the session ends.

    Called by cleanup_expired_sessions() and the cancel route.
    Keeps app/static/qr/ from accumulating stale images.

    Returns True if deleted, False if file didn't exist.
    """
    filepath = os.path.join(QR_FOLDER, f'{session_id}.png')
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


# ══════════════════════════════════════════════════════════════════════
#  HELPER: cleanup_expired_sessions
# ══════════════════════════════════════════════════════════════════════

def cleanup_expired_sessions() -> int:
    """
    Remove expired sessions from _sessions and delete their PNG files.

    Called automatically at the start of every create_session() call
    (lazy cleanup — no scheduler needed).

    Returns count of sessions removed.
    """
    now     = datetime.utcnow()
    expired = [
        sid for sid, sess in _sessions.items()
        if sess['expires_at'] < now
    ]
    for sid in expired:
        delete_qr_image(sid)
        del _sessions[sid]

    return len(expired)