# # """
# # QR SERVICE
# # ==========
# # Handles creation and validation of QR code attendance sessions.

# # HOW IT FITS INTO THE EXISTING SYSTEM
# # ──────────────────────────────────────
# # The existing mark_attendance() in teacher_service.py is the
# # single source of truth for writing attendance records. This service
# # does NOT replace or duplicate that logic. It only:

# #   1. Creates a short-lived session that authorises ONE class
# #   2. Validates whether that session is still alive
# #   3. Hands off to the existing mark_attendance() when a student scans

# # Think of this service as the "gatekeeper". Once a student passes
# # the gate (valid session + enrolled + not duplicate), the existing
# # attendance pipeline takes over exactly as if a teacher had clicked
# # the form manually.

# # STORAGE CHOICE: IN-MEMORY DICTIONARY
# # ──────────────────────────────────────
# # Sessions are stored in a plain Python dict called _sessions.
# # This is intentional at this stage because:

# #   • QR sessions are TEMPORARY — they live for 5 minutes only.
# #     Storing them in the database would mean constantly inserting
# #     and then querying rows that become useless immediately.
# #   • Simplicity — no migration, no new table, no ORM query needed
# #     to create or look up a session.
# #   • Speed — dict lookup is O(1). No DB round-trip on every scan.

# # TRADE-OFF:
# #   In-memory storage is lost if the server restarts.
# #   For a production multi-server setup (step 14.x), we would move
# #   to Redis — the interface stays the same, only the storage backend
# #   changes. That migration is a 5-line swap.

# # DATA FLOW REMINDER (from Step 14.1 design):
# #   Teacher generates QR → session created here
# #   Student scans QR    → session validated here → mark_attendance() called
# # """

# # import uuid
# # import os
# # import qrcode
# # from datetime import datetime, timedelta


# # # ══════════════════════════════════════════════════════════════════════
# # #  CONSTANTS
# # #  Change these values if college policy changes — one place only.
# # # ══════════════════════════════════════════════════════════════════════

# # QR_EXPIRY_MINUTES = 2
# # # How long a QR code stays valid after generation.
# # # After this window, any student who tries to scan gets "QR expired".

# # # ── QR IMAGE STORAGE ─────────────────────────────────────────────────
# # # This is the folder INSIDE app/static/ where QR images are saved.
# # # Flask serves everything inside app/static/ automatically at /static/...
# # # So a file at app/static/qr/abc.png is accessible at /static/qr/abc.png
# # #
# # # We compute the absolute path at module load time using __file__:
# # #   __file__ = .../app/services/qr_service.py
# # #   os.path.dirname(__file__) = .../app/services/
# # #   go up one level = .../app/
# # #   then join 'static/qr' = .../app/static/qr/
# # #
# # # Using __file__ instead of a hardcoded path means this works
# # # regardless of where the server is deployed.

# # _SERVICE_DIR  = os.path.dirname(os.path.abspath(__file__))  # .../app/services
# # _APP_DIR      = os.path.dirname(_SERVICE_DIR)                # .../app
# # QR_FOLDER     = os.path.join(_APP_DIR, 'static', 'qr')      # .../app/static/qr

# # # ── SCAN BASE URL ─────────────────────────────────────────────────────
# # # The full URL the QR code will encode.
# # # Student's phone opens this URL when they scan.
# # #
# # # In development:  http://localhost:5000
# # # In production:   https://yourcollege.edu
# # #
# # # We read from environment variable QR_BASE_URL if set,
# # # otherwise fall back to localhost for development.
# # # Change this in your .env file for production deployment.

# # QR_BASE_URL = os.environ.get('QR_BASE_URL', 'http://localhost:5000')
# # # The route /scan/<session_id> is appended by generate_qr_image().
# # # Final encoded URL: http://localhost:5000/scan/<uuid>


# # # ══════════════════════════════════════════════════════════════════════
# # #  IN-MEMORY SESSION STORE
# # #
# # #  _sessions is a module-level dictionary.
# # #  "Module-level" means it lives as long as the Flask server process
# # #  runs — it is NOT re-created on each request.
# # #
# # #  Structure:
# # #  {
# # #    "f47ac10b-58cc-4372-a567-0e02b2c3d479": {
# # #        "session_id"  : "f47ac10b-58cc-4372-a567-0e02b2c3d479",
# # #        "subject_id"  : 3,
# # #        "teacher_id"  : 7,
# # #        "created_at"  : datetime(2025, 4, 3, 10, 30, 0),
# # #        "expires_at"  : datetime(2025, 4, 3, 10, 35, 0),
# # #        "is_active"   : True,
# # #        "scan_count"  : 0,
# # #    },
# # #    ...
# # #  }
# # #
# # #  Key   = session_id string (UUID)
# # #  Value = dict of session details
# # # ══════════════════════════════════════════════════════════════════════

# # _sessions = {}
# # # The underscore prefix is a Python convention meaning "internal to
# # # this module — don't import or use this directly from outside".


# # # ══════════════════════════════════════════════════════════════════════
# # #  FUNCTION 1: create_session
# # # ══════════════════════════════════════════════════════════════════════

# # def create_session(teacher_id: int, subject_id: int) -> dict:
# #     """
# #     Create a new QR code attendance session.

# #     Called when: a teacher clicks "Generate QR" for a subject.

# #     What it does:
# #       1. Generates a UUID4 — a random 36-character string that is
# #          practically impossible to guess (122 bits of randomness).
# #          Example: "f47ac10b-58cc-4372-a567-0e02b2c3d479"

# #       2. Calculates the expiry timestamp:
# #          expires_at = now + 5 minutes

# #       3. Stores the session in _sessions under the UUID key.

# #       4. Returns the full session dict so the caller (route) can
# #          build the QR URL and display the countdown.

# #     Parameters:
# #       teacher_id  — the Teacher.id (NOT User.id) of the teacher
# #                     generating the QR. Stored so we know WHO authorised
# #                     this session when the attendance record is written.
# #       subject_id  — the Subject.id this QR is for.

# #     Returns:
# #       A dict with all session fields. The caller uses 'session_id'
# #       to build the URL: /scan/<session_id>

# #     Example return value:
# #       {
# #         'session_id': 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
# #         'subject_id': 3,
# #         'teacher_id': 7,
# #         'created_at': datetime(2025, 4, 3, 10, 30, 0),
# #         'expires_at': datetime(2025, 4, 3, 10, 35, 0),
# #         'is_active' : True,
# #         'scan_count': 0,
# #       }
# #     """
# #     # ── Step 1: Generate a UUID ──────────────────────────────────────
# #     # uuid.uuid4() creates a random UUID every time it is called.
# #     # str() converts it from a UUID object to a plain string like:
# #     # "f47ac10b-58cc-4372-a567-0e02b2c3d479"
# #     session_id = str(uuid.uuid4())

# #     # ── Step 2: Calculate timestamps ────────────────────────────────
# #     # datetime.utcnow() gives the current UTC time.
# #     # We always use UTC (not local time) so the server works the same
# #     # regardless of which timezone it's deployed in.
# #     now        = datetime.utcnow()
# #     expires_at = now + timedelta(minutes=QR_EXPIRY_MINUTES)

# #     # ── Step 3: Build the session dict ──────────────────────────────
# #     # ── Step 3: Generate the QR image file ─────────────────────────
# #     # generate_qr_image() encodes the scan URL into a PNG and saves it
# #     # to app/static/qr/<session_id>.png.
# #     # It returns the relative path 'qr/<session_id>.png' so the
# #     # template can use it with url_for('static', filename=image_path).
# #     image_path = generate_qr_image(session_id)

# #     # ── Step 4: Build the session dict ──────────────────────────────
# #     session = {
# #         'session_id' : session_id,
# #         'subject_id' : subject_id,
# #         'teacher_id' : teacher_id,
# #         'created_at' : now,
# #         'expires_at' : expires_at,
# #         'is_active'  : True,
# #         # is_active = True means this QR can still be scanned.
# #         # It becomes False if:
# #         #   a) The teacher manually cancels it
# #         #   b) We decide to deactivate it after expiry cleanup
# #         'scan_count' : 0,
# #         # Counts how many students have successfully scanned.
# #         # Displayed on the teacher's QR page: "12 students scanned"
# #         'image_path' : image_path,
# #         # Relative path to the QR PNG file inside app/static/.
# #         # Example: 'qr/f47ac10b-58cc-4372-a567-0e02b2c3d479.png'
# #         # Template usage:
# #         #   <img src="{{ url_for('static', filename=session.image_path) }}">
# #     }

# #     # ── Step 5: Store in the in-memory dict ─────────────────────────
# #     _sessions[session_id] = session

# #     return session


# # # ══════════════════════════════════════════════════════════════════════
# # #  FUNCTION 2: validate_session
# # # ══════════════════════════════════════════════════════════════════════

# # def validate_session(session_id: str) -> tuple:
# #     """
# #     Validate a QR session when a student scans the code.

# #     Called when: a student's browser hits /scan/<session_id>

# #     Three things are checked in order:

# #       CHECK 1 — Does it exist?
# #         Look up session_id in _sessions.
# #         If not found: someone typed a wrong URL or the server restarted.
# #         → Return (None, 'QR code not found. Please ask your teacher
# #                           to generate a new one.')

# #       CHECK 2 — Has it been cancelled?
# #         If is_active is False: teacher manually stopped the session.
# #         → Return (None, 'This QR session has been cancelled.')

# #       CHECK 3 — Has it expired?
# #         Compare expires_at with datetime.utcnow().
# #         If expires_at <= now: the 5-minute window has passed.
# #         → Return (None, 'QR code has expired. Ask teacher for a new one.')

# #       ALL PASS → Return (session_dict, None)

# #     Parameters:
# #       session_id — the UUID string from the URL

# #     Returns a TUPLE: (session_or_None, error_message_or_None)

# #       Success:  (session_dict, None)
# #       Failure:  (None, "reason string")

# #     Why return a tuple instead of raising an exception?
# #       This is the same pattern used throughout this codebase
# #       (see auth_service.authenticate_user, graduation_service.graduate_student).
# #       The caller (route) decides what to show the user — the service just
# #       says what happened.
# #     """
# #     # ── Check 1: Does the session exist? ────────────────────────────
# #     # dict.get() returns None if the key is not found.
# #     # This is safer than _sessions[session_id] which raises KeyError.
# #     session = _sessions.get(session_id)

# #     if session is None:
# #         return None, (
# #             'QR code not found. '
# #             'It may have been generated on a different server session. '
# #             'Please ask your teacher to generate a new QR code.'
# #         )

# #     # ── Check 2: Has the teacher cancelled it? ──────────────────────
# #     if not session['is_active']:
# #         return None, (
# #             'This QR session has been cancelled by the teacher.'
# #         )

# #     # ── Check 3: Has it expired? ─────────────────────────────────────
# #     # datetime.utcnow() is called HERE (not at creation time) so we
# #     # always compare against the current moment, not a stored snapshot.
# #     now = datetime.utcnow()

# #     if session['expires_at'] <= now:
# #         # Mark it inactive so future scans get "cancelled" not "expired"
# #         # (avoids running the expiry arithmetic repeatedly)
# #         _sessions[session_id]['is_active'] = False

# #         # Calculate how many minutes ago it expired — helpful message
# #         minutes_ago = int((now - session['expires_at']).total_seconds() / 60)
# #         ago_text    = f'{minutes_ago} minute(s) ago' if minutes_ago > 0 else 'just now'

# #         return None, (
# #             f'QR code expired {ago_text}. '
# #             f'QR codes are only valid for {QR_EXPIRY_MINUTES} minutes. '
# #             f'Please ask your teacher to generate a new one.'
# #         )

# #     # ── All checks passed ────────────────────────────────────────────
# #     return session, None


# # # ══════════════════════════════════════════════════════════════════════
# # #  FUNCTION 3: deactivate_session
# # # ══════════════════════════════════════════════════════════════════════

# # def deactivate_session(session_id: str) -> bool:
# #     """
# #     Teacher manually cancels a QR session before it expires.

# #     Used when: teacher ends class early and doesn't want more scans.

# #     Sets is_active = False in the stored session.
# #     After this, validate_session() will return the "cancelled" error
# #     for any student who tries to scan.

# #     Returns:
# #       True  — session was found and deactivated
# #       False — session not found (already gone or wrong ID)
# #     """
# #     session = _sessions.get(session_id)
# #     if session is None:
# #         return False

# #     _sessions[session_id]['is_active'] = False
# #     return True


# # # ══════════════════════════════════════════════════════════════════════
# # #  FUNCTION 4: increment_scan_count
# # # ══════════════════════════════════════════════════════════════════════

# # def increment_scan_count(session_id: str):
# #     """
# #     Increment the scan counter after a student successfully scans.

# #     Called by the route after attendance is marked successfully.
# #     The teacher's QR display page reads this number to show
# #     real-time progress: "14 of 42 students scanned".

# #     This is separate from validate_session() because we only want to
# #     count SUCCESSFUL scans — not failed attempts (expired, wrong student, etc.)
# #     """
# #     if session_id in _sessions:
# #         _sessions[session_id]['scan_count'] += 1


# # # ══════════════════════════════════════════════════════════════════════
# # #  FUNCTION 5: get_session
# # # ══════════════════════════════════════════════════════════════════════

# # def get_session(session_id: str) -> dict | None:
# #     """
# #     Retrieve a session dict by ID without any validation.

# #     Used by:
# #       - The teacher's QR display page to read scan_count and time_remaining
# #       - The deactivate route to confirm the session belongs to this teacher

# #     Returns None if session_id doesn't exist.
# #     """
# #     return _sessions.get(session_id)


# # # ══════════════════════════════════════════════════════════════════════
# # #  FUNCTION 6: get_time_remaining
# # # ══════════════════════════════════════════════════════════════════════

# # def get_time_remaining(session_id: str) -> int:
# #     """
# #     Return the number of whole seconds remaining on a QR session.

# #     Used by the teacher's QR page to power the countdown timer.
# #     The page calls this via AJAX every second to keep the display accurate.

# #     Returns:
# #       Positive int  — seconds remaining
# #       0             — expired (or session not found)
# #     """
# #     session = _sessions.get(session_id)
# #     if session is None:
# #         return 0

# #     remaining = (session['expires_at'] - datetime.utcnow()).total_seconds()
# #     return max(0, int(remaining))



# # # ══════════════════════════════════════════════════════════════════════
# # #  FUNCTION 7: generate_qr_image
# # # ══════════════════════════════════════════════════════════════════════

# # def generate_qr_image(session_id: str) -> str:
# #     """
# #     Generate a QR code PNG image for a session and save it to disk.

# #     HOW A QR CODE IS BUILT
# #     ───────────────────────
# #     A QR code is a 2D grid of black and white squares. Each square
# #     is called a "module". The pattern encodes the URL string using
# #     Reed-Solomon error correction so the code can still be read
# #     even if part of it is obscured (scratched, dirty, printed badly).

# #     The qrcode library handles all of this automatically. We just
# #     give it the URL string and it returns an image object.

# #     PARAMETERS EXPLAINED
# #     ─────────────────────
# #     version : int (1–40)
# #         Controls the size of the QR grid.
# #         version=1 → 21×21 modules (tiny, good for short URLs)
# #         version=None + fit=True → library picks the smallest version
# #         that fits our URL. We use this because the UUID URL is ~50 chars
# #         and version 1 is too small for it.

# #     error_correction : constant
# #         How much of the QR can be damaged and still be readable.
# #         ERROR_CORRECT_L → 7%  can be damaged (smaller, faster to scan)
# #         ERROR_CORRECT_M → 15% can be damaged  ← WE USE THIS
# #         ERROR_CORRECT_Q → 25% can be damaged
# #         ERROR_CORRECT_H → 30% can be damaged (bigger, slower to scan)
# #         M is the sweet spot for a phone screen display.

# #     box_size : int
# #         How many pixels each module (black/white square) takes.
# #         box_size=10 → each square is 10×10 pixels.
# #         Larger = bigger image = easier to scan from a distance.
# #         For a classroom projector display, 10 is a good choice.

# #     border : int
# #         The "quiet zone" — white space around the QR code in modules.
# #         The QR standard requires at least 4 modules of white border.
# #         We use 4 (the minimum) to keep the image compact.

# #     WHAT GETS SAVED
# #     ────────────────
# #     The image is saved as a PNG file at:
# #       app/static/qr/<session_id>.png

# #     For example:
# #       app/static/qr/f47ac10b-58cc-4372-a567-0e02b2c3d479.png

# #     Flask serves it at URL:
# #       /static/qr/f47ac10b-58cc-4372-a567-0e02b2c3d479.png

# #     In a template, the image tag looks like:
# #       <img src="{{ url_for('static', filename='qr/' + session_id + '.png') }}">

# #     WHAT IS RETURNED
# #     ─────────────────
# #     The function returns the RELATIVE path from the static folder:
# #       'qr/<session_id>.png'

# #     This is exactly what url_for('static', filename=...) expects.
# #     The route passes this string to the template, which plugs it
# #     into url_for to build the full HTTP URL for the browser.

# #     Parameters:
# #       session_id — the UUID string for this QR session

# #     Returns:
# #       str — relative path like 'qr/f47ac10b-....png'
# #             (relative to app/static/, usable with url_for)

# #     Raises:
# #       No exceptions raised — errors are caught and re-raised as
# #       RuntimeError with a clear message.
# #     """
# #     # ── Step 1: Make sure the qr/ folder exists ──────────────────────
# #     # os.makedirs() creates the folder AND any missing parent folders.
# #     # exist_ok=True means: if the folder already exists, do nothing
# #     # (don't raise an error). Without exist_ok=True, the second call
# #     # would crash with FileExistsError.
# #     os.makedirs(QR_FOLDER, exist_ok=True)

# #     # ── Step 2: Build the full URL this QR will encode ───────────────
# #     # Example: "http://localhost:5000/scan/f47ac10b-58cc-4372-a567-0e02b2c3d479"
# #     #
# #     # When a student scans this with their phone camera, the camera
# #     # app reads the URL and opens it in the browser. The browser
# #     # then hits our Flask route /scan/<session_id>.
# #     scan_url = f'{QR_BASE_URL}/scan/{session_id}'

# #     # ── Step 3: Create the QR code object ────────────────────────────
# #     # qrcode.QRCode gives us fine-grained control over the settings.
# #     # (qrcode.make() is the shortcut but uses defaults we don't want.)
# #     qr = qrcode.QRCode(
# #         version          = None,                        # auto-detect
# #         error_correction = qrcode.constants.ERROR_CORRECT_M,
# #         box_size         = 10,                          # pixels per module
# #         border           = 4,                           # quiet zone modules
# #     )

# #     # ── Step 4: Add the URL data ──────────────────────────────────────
# #     # qr.add_data() feeds the string into the QR encoder.
# #     # qr.make(fit=True) runs the encoding and picks the smallest
# #     # QR version that can hold all the data without overflowing.
# #     qr.add_data(scan_url)
# #     qr.make(fit=True)

# #     # ── Step 5: Render as a PIL image ────────────────────────────────
# #     # make_image() converts the encoded data into an actual pixel image.
# #     # fill_color = black modules (the dark squares)
# #     # back_color = white background
# #     img = qr.make_image(fill_color='black', back_color='white')

# #     # ── Step 6: Build the file path and save ─────────────────────────
# #     # filename:    "f47ac10b-58cc-4372-a567-0e02b2c3d479.png"
# #     # full path:   ".../app/static/qr/f47ac10b-....png"
# #     # static path: "qr/f47ac10b-....png"  ← what we return

# #     filename    = f'{session_id}.png'
# #     full_path   = os.path.join(QR_FOLDER, filename)
# #     static_path = f'qr/{filename}'        # relative to app/static/

# #     # img.save() writes the PNG bytes to the file system.
# #     # PIL/Pillow infers the format from the .png extension.
# #     img.save(full_path)

# #     return static_path


# # # ══════════════════════════════════════════════════════════════════════
# # #  FUNCTION 8: delete_qr_image
# # # ══════════════════════════════════════════════════════════════════════

# # def delete_qr_image(session_id: str) -> bool:
# #     """
# #     Delete the QR image file from disk when the session ends.

# #     WHY DELETE:
# #     QR images serve no purpose once the session expires — the session
# #     is gone from memory, so even if someone kept the image and tried
# #     to scan it later, validate_session() would return "not found".
# #     Deleting the file keeps the static/qr/ folder clean.

# #     Called by: the cleanup_expired_sessions() function, and optionally
# #     by the deactivate route when a teacher manually cancels.

# #     Returns:
# #       True  — file was found and deleted
# #       False — file didn't exist (already deleted or never created)
# #     """
# #     filepath = os.path.join(QR_FOLDER, f'{session_id}.png')
# #     if os.path.exists(filepath):
# #         os.remove(filepath)
# #         return True
# #     return False

# # # ══════════════════════════════════════════════════════════════════════
# # #  HELPER: cleanup_expired_sessions
# # # ══════════════════════════════════════════════════════════════════════

# # def cleanup_expired_sessions():
# #     """
# #     Remove all expired sessions from the in-memory dict.

# #     WHY: The dict grows by one entry every time a teacher generates
# #     a QR. Without cleanup, it would slowly fill up memory over a
# #     full day of teaching. Since sessions only need to live for
# #     5 minutes, anything older than that is safe to remove.

# #     WHEN TO CALL: This should be called periodically — for example,
# #     at the START of each create_session() call (lazy cleanup), or
# #     on a scheduled task. We use the lazy approach here: every time
# #     a new session is created, old ones are swept out.

# #     We do NOT call this in validate_session() to keep that function
# #     fast — it only does the minimum work needed to answer yes/no.
# #     """
# #     now     = datetime.utcnow()
# #     # Build a list of keys to delete (can't modify dict while iterating it)
# #     expired = [
# #         sid for sid, sess in _sessions.items()
# #         if sess['expires_at'] < now
# #     ]
# #     for sid in expired:
# #         # Also delete the QR image file so static/qr/ stays clean
# #         delete_qr_image(sid)
# #         del _sessions[sid]

# #     return len(expired)    # return count for logging/debugging


# # # ══════════════════════════════════════════════════════════════════════
# # #  Patch create_session to auto-cleanup
# # # ══════════════════════════════════════════════════════════════════════
# # # Wrap the original create_session to always sweep expired entries first.
# # # This keeps memory clean without any external scheduler.

# # _original_create = create_session

# # def create_session(teacher_id: int, subject_id: int) -> dict:
# #     """
# #     (Auto-cleanup wrapper around the core create_session logic.)
# #     Sweeps expired sessions before creating a new one.
# #     See the internal function above for full documentation.
# #     """
# #     cleanup_expired_sessions()     # remove stale entries first
# #     return _original_create(teacher_id, subject_id)


# ############-------------update---------------
# """
# QR SERVICE
# ==========
# Handles QR code generation (teacher side) and token validation (student side).

# Teacher flow:
#   generate_qr_session()  → creates QRSession, returns PNG path + token
#   close_qr_session()     → marks session inactive

# Student flow:
#   validate_qr_token()    → checks token exists, is valid, not already marked
#   mark_attendance_via_qr() → records Attendance row for the student
# """

# import os
# import uuid
# import qrcode
# from datetime import datetime, date

# from app import db
# from app.models.qr_session  import QRSession
# from app.models.attendance   import Attendance
# from app.models.subject      import Subject
# from app.models.student      import Student


# # ======================================================================
# #  TEACHER SIDE — generate / close sessions
# # ======================================================================

# def generate_qr_session(teacher_user, subject_id, expiry_minutes=15,
#                         attendance_date=None, base_url=''):
#     """
#     Create a new QRSession and render the QR code PNG.

#     Returns:
#         (qr_session, qr_image_url, None)   on success
#         (None, None, error_message)         on failure
#     """
#     from app.decorators import teacher_owns_subject  # avoid circular import

#     teacher = teacher_user.teacher_profile
#     if not teacher:
#         return None, None, 'Teacher profile not found.'

#     # Verify the teacher is assigned to this subject
#     subject = Subject.query.get(subject_id)
#     if not subject:
#         return None, None, 'Subject not found.'

#     # HODs can generate for any subject in their department
#     if not teacher_user.is_hod:
#         assigned_ids = [s.id for s in teacher.subjects.all()]
#         if subject_id not in assigned_ids:
#             return None, None, 'You are not assigned to teach this subject.'

#     if attendance_date is None:
#         attendance_date = date.today()

#     # Create the session row
#     session = QRSession(
#         subject_id      = subject_id,
#         teacher_id      = teacher.id,
#         attendance_date = attendance_date,
#         expiry_minutes  = expiry_minutes,
#     )
#     db.session.add(session)
#     db.session.flush()   # get session.token without committing yet

#     # Build the URL that will be encoded in the QR code
#     scan_url = f'{base_url}/student/scan?token={session.token}'

#     # Render and save the QR code PNG
#     qr_img_path, error = _render_qr_png(session.token, scan_url)
#     if error:
#         db.session.rollback()
#         return None, None, error

#     db.session.commit()

#     # Return the relative URL for use in <img src="...">
#     qr_image_url = f'/static/qr/{session.token}.png'
#     return session, qr_image_url, None


# def close_qr_session(teacher_user, session_id):
#     """
#     Mark a session inactive so students can no longer scan.
#     Returns (True, None) or (False, error_msg).
#     """
#     session = QRSession.query.get(session_id)
#     if not session:
#         return False, 'Session not found.'

#     teacher = teacher_user.teacher_profile
#     if not teacher or session.teacher_id != teacher.id:
#         return False, 'You do not own this session.'

#     session.deactivate()
#     db.session.commit()
#     return True, None


# # ======================================================================
# #  STUDENT SIDE — validate token and mark attendance
# # ======================================================================

# def validate_qr_token(token):
#     """
#     Look up the token and check it is still valid.

#     Returns:
#         (qr_session, None)       if the session is open and valid
#         (None, error_message)    if anything is wrong
#     """
#     session = QRSession.query.filter_by(token=token).first()

#     if not session:
#         return None, 'Invalid QR code. Please ask your teacher to generate a new one.'

#     if not session.is_active:
#         return None, 'This QR session has been closed by the teacher.'

#     if session.is_expired:
#         return None, (
#             f'This QR code expired {session.expiry_minutes} minutes after it was generated. '
#             'Please ask your teacher for a new one.'
#         )

#     return session, None


# def mark_attendance_via_qr(student_user, token):
#     """
#     Record the student as PRESENT for the subject/date linked to this token.

#     Returns:
#         (attendance_record, qr_session, None)    on success
#         (None, None, error_message)               on failure
#     """
#     # 1. Validate the token
#     qr_session, error = validate_qr_token(token)
#     if error:
#         return None, None, error

#     student = student_user.student_profile
#     if not student:
#         return None, None, 'Student profile not found. Contact admin.'

#     subject = qr_session.subject

#     # 2. Verify the student is enrolled in this subject
#     enrolled = (
#         subject.department_id == student.department_id
#         and subject.semester   == student.semester
#         and subject.program_type == student.program_type
#         and subject.is_active
#     )
#     if not enrolled:
#         return None, None, (
#             f'You are not enrolled in {subject.name} ({subject.code}). '
#             'Contact your HOD if this is a mistake.'
#         )

#     # 3. Check for duplicate (already marked for this subject+date)
#     existing = Attendance.query.filter_by(
#         student_id  = student.id,
#         subject_id  = subject.id,
#         date        = qr_session.attendance_date,
#     ).first()

#     if existing:
#         return None, qr_session, None   # already marked — return session so template shows info

#     # 4. Create the attendance record
#     #    marked_by_id is the teacher who owns the QR session
#     teacher_user_obj = qr_session.teacher.user
#     record = Attendance(
#         student_id   = student.id,
#         subject_id   = subject.id,
#         date         = qr_session.attendance_date,
#         semester     = student.semester,
#         status       = 'present',
#         marked_by_id = teacher_user_obj.id,
#         notes        = f'QR scan (session {qr_session.token[:8]})',
#     )
#     db.session.add(record)
#     db.session.commit()

#     return record, qr_session, None


# # ======================================================================
# #  INTERNAL HELPERS
# # ======================================================================

# def _render_qr_png(token, scan_url):
#     """
#     Generate a QR code PNG and save it to app/static/qr/<token>.png

#     Returns (file_path, None) or (None, error_message).
#     """
#     try:
#         qr = qrcode.QRCode(
#             version          = 1,
#             error_correction = qrcode.constants.ERROR_CORRECT_L,
#             box_size         = 10,
#             border           = 4,
#         )
#         qr.add_data(scan_url)
#         qr.make(fit=True)
#         img = qr.make_image(fill_color='black', back_color='white')

#         # Save into app/static/qr/
#         static_dir = os.path.join(
#             os.path.dirname(__file__),   # app/services/
#             '..', 'static', 'qr'
#         )
#         os.makedirs(static_dir, exist_ok=True)
#         file_path = os.path.join(static_dir, f'{token}.png')
#         img.save(file_path)
#         return file_path, None

#     except Exception as exc:
#         return None, f'Failed to generate QR image: {exc}'

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
  3. Hands off to the existing mark_attendance() when a student scans

Think of this service as the "gatekeeper". Once a student passes
the gate (valid session + enrolled + not duplicate), the existing
attendance pipeline takes over exactly as if a teacher had clicked
the form manually.

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
  For a production multi-server setup (step 14.x), we would move
  to Redis — the interface stays the same, only the storage backend
  changes. That migration is a 5-line swap.

DATA FLOW REMINDER (from Step 14.1 design):
  Teacher generates QR → session created here
  Student scans QR    → session validated here → mark_attendance() called
"""

import uuid
import os
import qrcode
from datetime import datetime, timedelta


# ══════════════════════════════════════════════════════════════════════
#  CONSTANTS
#  Change these values if college policy changes — one place only.
# ══════════════════════════════════════════════════════════════════════

QR_EXPIRY_MINUTES = 2
# How long a QR code stays valid after generation.
# After this window, any student who tries to scan gets "QR expired".

# ── QR IMAGE STORAGE ─────────────────────────────────────────────────
# This is the folder INSIDE app/static/ where QR images are saved.
# Flask serves everything inside app/static/ automatically at /static/...
# So a file at app/static/qr/abc.png is accessible at /static/qr/abc.png
#
# We compute the absolute path at module load time using __file__:
#   __file__ = .../app/services/qr_service.py
#   os.path.dirname(__file__) = .../app/services/
#   go up one level = .../app/
#   then join 'static/qr' = .../app/static/qr/
#
# Using __file__ instead of a hardcoded path means this works
# regardless of where the server is deployed.

_SERVICE_DIR  = os.path.dirname(os.path.abspath(__file__))  # .../app/services
_APP_DIR      = os.path.dirname(_SERVICE_DIR)                # .../app
QR_FOLDER     = os.path.join(_APP_DIR, 'static', 'qr')      # .../app/static/qr

# ── SCAN BASE URL ─────────────────────────────────────────────────────
# The full URL the QR code will encode.
# Student's phone opens this URL when they scan.
#
# In development:  http://localhost:5000
# In production:   https://yourcollege.edu
#
# We read from environment variable QR_BASE_URL if set,
# otherwise fall back to localhost for development.
# Change this in your .env file for production deployment.

QR_BASE_URL = os.environ.get('QR_BASE_URL', 'http://localhost:5000')
# The route /scan/<session_id> is appended by generate_qr_image().
# Final encoded URL: http://localhost:5000/scan/<uuid>


# ══════════════════════════════════════════════════════════════════════
#  IN-MEMORY SESSION STORE
#
#  _sessions is a module-level dictionary.
#  "Module-level" means it lives as long as the Flask server process
#  runs — it is NOT re-created on each request.
#
#  Structure:
#  {
#    "f47ac10b-58cc-4372-a567-0e02b2c3d479": {
#        "session_id"  : "f47ac10b-58cc-4372-a567-0e02b2c3d479",
#        "subject_id"  : 3,
#        "teacher_id"  : 7,
#        "created_at"  : datetime(2025, 4, 3, 10, 30, 0),
#        "expires_at"  : datetime(2025, 4, 3, 10, 35, 0),
#        "is_active"   : True,
#        "scan_count"  : 0,
#    },
#    ...
#  }
#
#  Key   = session_id string (UUID)
#  Value = dict of session details
# ══════════════════════════════════════════════════════════════════════

_sessions = {}
# The underscore prefix is a Python convention meaning "internal to
# this module — don't import or use this directly from outside".


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 1: create_session
# ══════════════════════════════════════════════════════════════════════

def create_session(teacher_id: int, subject_id: int) -> dict:
    """
    Create a new QR code attendance session.

    Called when: a teacher clicks "Generate QR" for a subject.

    What it does:
      1. Generates a UUID4 — a random 36-character string that is
         practically impossible to guess (122 bits of randomness).
         Example: "f47ac10b-58cc-4372-a567-0e02b2c3d479"

      2. Calculates the expiry timestamp:
         expires_at = now + 5 minutes

      3. Stores the session in _sessions under the UUID key.

      4. Returns the full session dict so the caller (route) can
         build the QR URL and display the countdown.

    Parameters:
      teacher_id  — the Teacher.id (NOT User.id) of the teacher
                    generating the QR. Stored so we know WHO authorised
                    this session when the attendance record is written.
      subject_id  — the Subject.id this QR is for.

    Returns:
      A dict with all session fields. The caller uses 'session_id'
      to build the URL: /scan/<session_id>

    Example return value:
      {
        'session_id': 'f47ac10b-58cc-4372-a567-0e02b2c3d479',
        'subject_id': 3,
        'teacher_id': 7,
        'created_at': datetime(2025, 4, 3, 10, 30, 0),
        'expires_at': datetime(2025, 4, 3, 10, 35, 0),
        'is_active' : True,
        'scan_count': 0,
      }
    """
    # ── Step 1: Generate a UUID ──────────────────────────────────────
    # uuid.uuid4() creates a random UUID every time it is called.
    # str() converts it from a UUID object to a plain string like:
    # "f47ac10b-58cc-4372-a567-0e02b2c3d479"
    session_id = str(uuid.uuid4())

    # ── Step 2: Calculate timestamps ────────────────────────────────
    # datetime.utcnow() gives the current UTC time.
    # We always use UTC (not local time) so the server works the same
    # regardless of which timezone it's deployed in.
    now        = datetime.utcnow()
    expires_at = now + timedelta(minutes=QR_EXPIRY_MINUTES)

    # ── Step 3: Build the session dict ──────────────────────────────
    # ── Step 3: Generate the QR image file ─────────────────────────
    # generate_qr_image() encodes the scan URL into a PNG and saves it
    # to app/static/qr/<session_id>.png.
    # It returns the relative path 'qr/<session_id>.png' so the
    # template can use it with url_for('static', filename=image_path).
    image_path = generate_qr_image(session_id)

    # ── Step 4: Build the session dict ──────────────────────────────
    session = {
        'session_id' : session_id,
        'subject_id' : subject_id,
        'teacher_id' : teacher_id,
        'created_at' : now,
        'expires_at' : expires_at,
        'is_active'  : True,
        # is_active = True means this QR can still be scanned.
        # It becomes False if:
        #   a) The teacher manually cancels it
        #   b) We decide to deactivate it after expiry cleanup
        'scan_count' : 0,
        # Counts how many students have successfully scanned.
        # Displayed on the teacher's QR page: "12 students scanned"
        'image_path' : image_path,
        # Relative path to the QR PNG file inside app/static/.
        # Example: 'qr/f47ac10b-58cc-4372-a567-0e02b2c3d479.png'
        # Template usage:
        #   <img src="{{ url_for('static', filename=session.image_path) }}">
    }

    # ── Step 5: Store in the in-memory dict ─────────────────────────
    _sessions[session_id] = session

    return session


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 2: validate_session
# ══════════════════════════════════════════════════════════════════════

def validate_session(session_id: str) -> tuple:
    """
    Validate a QR session when a student scans the code.

    Called when: a student's browser hits /scan/<session_id>

    Three things are checked in order:

      CHECK 1 — Does it exist?
        Look up session_id in _sessions.
        If not found: someone typed a wrong URL or the server restarted.
        → Return (None, 'QR code not found. Please ask your teacher
                          to generate a new one.')

      CHECK 2 — Has it been cancelled?
        If is_active is False: teacher manually stopped the session.
        → Return (None, 'This QR session has been cancelled.')

      CHECK 3 — Has it expired?
        Compare expires_at with datetime.utcnow().
        If expires_at <= now: the 5-minute window has passed.
        → Return (None, 'QR code has expired. Ask teacher for a new one.')

      ALL PASS → Return (session_dict, None)

    Parameters:
      session_id — the UUID string from the URL

    Returns a TUPLE: (session_or_None, error_message_or_None)

      Success:  (session_dict, None)
      Failure:  (None, "reason string")

    Why return a tuple instead of raising an exception?
      This is the same pattern used throughout this codebase
      (see auth_service.authenticate_user, graduation_service.graduate_student).
      The caller (route) decides what to show the user — the service just
      says what happened.
    """
    # ── Check 1: Does the session exist? ────────────────────────────
    # dict.get() returns None if the key is not found.
    # This is safer than _sessions[session_id] which raises KeyError.
    session = _sessions.get(session_id)

    if session is None:
        return None, (
            'QR code not found. '
            'It may have been generated on a different server session. '
            'Please ask your teacher to generate a new QR code.'
        )

    # ── Check 2: Has the teacher cancelled it? ──────────────────────
    if not session['is_active']:
        return None, (
            'This QR session has been cancelled by the teacher.'
        )

    # ── Check 3: Has it expired? ─────────────────────────────────────
    # datetime.utcnow() is called HERE (not at creation time) so we
    # always compare against the current moment, not a stored snapshot.
    now = datetime.utcnow()

    if session['expires_at'] <= now:
        # Mark it inactive so future scans get "cancelled" not "expired"
        # (avoids running the expiry arithmetic repeatedly)
        _sessions[session_id]['is_active'] = False

        # Calculate how many minutes ago it expired — helpful message
        minutes_ago = int((now - session['expires_at']).total_seconds() / 60)
        ago_text    = f'{minutes_ago} minute(s) ago' if minutes_ago > 0 else 'just now'

        return None, (
            f'QR code expired {ago_text}. '
            f'QR codes are only valid for {QR_EXPIRY_MINUTES} minutes. '
            f'Please ask your teacher to generate a new one.'
        )

    # ── All checks passed ────────────────────────────────────────────
    return session, None


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 3: deactivate_session
# ══════════════════════════════════════════════════════════════════════

def deactivate_session(session_id: str) -> bool:
    """
    Teacher manually cancels a QR session before it expires.

    Used when: teacher ends class early and doesn't want more scans.

    Sets is_active = False in the stored session.
    After this, validate_session() will return the "cancelled" error
    for any student who tries to scan.

    Returns:
      True  — session was found and deactivated
      False — session not found (already gone or wrong ID)
    """
    session = _sessions.get(session_id)
    if session is None:
        return False

    _sessions[session_id]['is_active'] = False
    return True


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 4: increment_scan_count
# ══════════════════════════════════════════════════════════════════════

def increment_scan_count(session_id: str):
    """
    Increment the scan counter after a student successfully scans.

    Called by the route after attendance is marked successfully.
    The teacher's QR display page reads this number to show
    real-time progress: "14 of 42 students scanned".

    This is separate from validate_session() because we only want to
    count SUCCESSFUL scans — not failed attempts (expired, wrong student, etc.)
    """
    if session_id in _sessions:
        _sessions[session_id]['scan_count'] += 1


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 5: get_session
# ══════════════════════════════════════════════════════════════════════

def get_session(session_id: str) -> dict | None:
    """
    Retrieve a session dict by ID without any validation.

    Used by:
      - The teacher's QR display page to read scan_count and time_remaining
      - The deactivate route to confirm the session belongs to this teacher

    Returns None if session_id doesn't exist.
    """
    return _sessions.get(session_id)


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 6: get_time_remaining
# ══════════════════════════════════════════════════════════════════════

def get_time_remaining(session_id: str) -> int:
    """
    Return the number of whole seconds remaining on a QR session.

    Used by the teacher's QR page to power the countdown timer.
    The page calls this via AJAX every second to keep the display accurate.

    Returns:
      Positive int  — seconds remaining
      0             — expired (or session not found)
    """
    session = _sessions.get(session_id)
    if session is None:
        return 0

    remaining = (session['expires_at'] - datetime.utcnow()).total_seconds()
    return max(0, int(remaining))



# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 7: generate_qr_image
# ══════════════════════════════════════════════════════════════════════

def generate_qr_image(session_id: str) -> str:
    """
    Generate a QR code PNG image for a session and save it to disk.

    HOW A QR CODE IS BUILT
    ───────────────────────
    A QR code is a 2D grid of black and white squares. Each square
    is called a "module". The pattern encodes the URL string using
    Reed-Solomon error correction so the code can still be read
    even if part of it is obscured (scratched, dirty, printed badly).

    The qrcode library handles all of this automatically. We just
    give it the URL string and it returns an image object.

    PARAMETERS EXPLAINED
    ─────────────────────
    version : int (1–40)
        Controls the size of the QR grid.
        version=1 → 21×21 modules (tiny, good for short URLs)
        version=None + fit=True → library picks the smallest version
        that fits our URL. We use this because the UUID URL is ~50 chars
        and version 1 is too small for it.

    error_correction : constant
        How much of the QR can be damaged and still be readable.
        ERROR_CORRECT_L → 7%  can be damaged (smaller, faster to scan)
        ERROR_CORRECT_M → 15% can be damaged  ← WE USE THIS
        ERROR_CORRECT_Q → 25% can be damaged
        ERROR_CORRECT_H → 30% can be damaged (bigger, slower to scan)
        M is the sweet spot for a phone screen display.

    box_size : int
        How many pixels each module (black/white square) takes.
        box_size=10 → each square is 10×10 pixels.
        Larger = bigger image = easier to scan from a distance.
        For a classroom projector display, 10 is a good choice.

    border : int
        The "quiet zone" — white space around the QR code in modules.
        The QR standard requires at least 4 modules of white border.
        We use 4 (the minimum) to keep the image compact.

    WHAT GETS SAVED
    ────────────────
    The image is saved as a PNG file at:
      app/static/qr/<session_id>.png

    For example:
      app/static/qr/f47ac10b-58cc-4372-a567-0e02b2c3d479.png

    Flask serves it at URL:
      /static/qr/f47ac10b-58cc-4372-a567-0e02b2c3d479.png

    In a template, the image tag looks like:
      <img src="{{ url_for('static', filename='qr/' + session_id + '.png') }}">

    WHAT IS RETURNED
    ─────────────────
    The function returns the RELATIVE path from the static folder:
      'qr/<session_id>.png'

    This is exactly what url_for('static', filename=...) expects.
    The route passes this string to the template, which plugs it
    into url_for to build the full HTTP URL for the browser.

    Parameters:
      session_id — the UUID string for this QR session

    Returns:
      str — relative path like 'qr/f47ac10b-....png'
            (relative to app/static/, usable with url_for)

    Raises:
      No exceptions raised — errors are caught and re-raised as
      RuntimeError with a clear message.
    """
    # ── Step 1: Make sure the qr/ folder exists ──────────────────────
    # os.makedirs() creates the folder AND any missing parent folders.
    # exist_ok=True means: if the folder already exists, do nothing
    # (don't raise an error). Without exist_ok=True, the second call
    # would crash with FileExistsError.
    os.makedirs(QR_FOLDER, exist_ok=True)

    # ── Step 2: Build the full URL this QR will encode ───────────────
    # Example: "http://localhost:5000/scan/f47ac10b-58cc-4372-a567-0e02b2c3d479"
    #
    # When a student scans this with their phone camera, the camera
    # app reads the URL and opens it in the browser. The browser
    # then hits our Flask route /scan/<session_id>.
    scan_url = f'{QR_BASE_URL}/scan/{session_id}'

    # ── Step 3: Create the QR code object ────────────────────────────
    # qrcode.QRCode gives us fine-grained control over the settings.
    # (qrcode.make() is the shortcut but uses defaults we don't want.)
    qr = qrcode.QRCode(
        version          = None,                        # auto-detect
        error_correction = qrcode.constants.ERROR_CORRECT_M,
        box_size         = 10,                          # pixels per module
        border           = 4,                           # quiet zone modules
    )

    # ── Step 4: Add the URL data ──────────────────────────────────────
    # qr.add_data() feeds the string into the QR encoder.
    # qr.make(fit=True) runs the encoding and picks the smallest
    # QR version that can hold all the data without overflowing.
    qr.add_data(scan_url)
    qr.make(fit=True)

    # ── Step 5: Render as a PIL image ────────────────────────────────
    # make_image() converts the encoded data into an actual pixel image.
    # fill_color = black modules (the dark squares)
    # back_color = white background
    img = qr.make_image(fill_color='black', back_color='white')

    # ── Step 6: Build the file path and save ─────────────────────────
    # filename:    "f47ac10b-58cc-4372-a567-0e02b2c3d479.png"
    # full path:   ".../app/static/qr/f47ac10b-....png"
    # static path: "qr/f47ac10b-....png"  ← what we return

    filename    = f'{session_id}.png'
    full_path   = os.path.join(QR_FOLDER, filename)
    static_path = f'qr/{filename}'        # relative to app/static/

    # img.save() writes the PNG bytes to the file system.
    # PIL/Pillow infers the format from the .png extension.
    img.save(full_path)

    return static_path


# ══════════════════════════════════════════════════════════════════════
#  FUNCTION 8: delete_qr_image
# ══════════════════════════════════════════════════════════════════════

def delete_qr_image(session_id: str) -> bool:
    """
    Delete the QR image file from disk when the session ends.

    WHY DELETE:
    QR images serve no purpose once the session expires — the session
    is gone from memory, so even if someone kept the image and tried
    to scan it later, validate_session() would return "not found".
    Deleting the file keeps the static/qr/ folder clean.

    Called by: the cleanup_expired_sessions() function, and optionally
    by the deactivate route when a teacher manually cancels.

    Returns:
      True  — file was found and deleted
      False — file didn't exist (already deleted or never created)
    """
    filepath = os.path.join(QR_FOLDER, f'{session_id}.png')
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False

# ══════════════════════════════════════════════════════════════════════
#  HELPER: cleanup_expired_sessions
# ══════════════════════════════════════════════════════════════════════

def cleanup_expired_sessions():
    """
    Remove all expired sessions from the in-memory dict.

    WHY: The dict grows by one entry every time a teacher generates
    a QR. Without cleanup, it would slowly fill up memory over a
    full day of teaching. Since sessions only need to live for
    5 minutes, anything older than that is safe to remove.

    WHEN TO CALL: This should be called periodically — for example,
    at the START of each create_session() call (lazy cleanup), or
    on a scheduled task. We use the lazy approach here: every time
    a new session is created, old ones are swept out.

    We do NOT call this in validate_session() to keep that function
    fast — it only does the minimum work needed to answer yes/no.
    """
    now     = datetime.utcnow()
    # Build a list of keys to delete (can't modify dict while iterating it)
    expired = [
        sid for sid, sess in _sessions.items()
        if sess['expires_at'] < now
    ]
    for sid in expired:
        # Also delete the QR image file so static/qr/ stays clean
        delete_qr_image(sid)
        del _sessions[sid]

    return len(expired)    # return count for logging/debugging


# ══════════════════════════════════════════════════════════════════════
#  Patch create_session to auto-cleanup
# ══════════════════════════════════════════════════════════════════════
# Wrap the original create_session to always sweep expired entries first.
# This keeps memory clean without any external scheduler.

_original_create = create_session

def create_session(teacher_id: int, subject_id: int) -> dict:
    """
    (Auto-cleanup wrapper around the core create_session logic.)
    Sweeps expired sessions before creating a new one.
    See the internal function above for full documentation.
    """
    cleanup_expired_sessions()     # remove stale entries first
    return _original_create(teacher_id, subject_id)