# from app import db
# from datetime import datetime
# import secrets

# class QRSession(db.Model):
#     """
#     One row = one QR attendance session created by a teacher.
#     The token is embedded in the QR code URL.
#     Students scan → hit /student/qr/<token> → attendance marked.
#     """
#     __tablename__ = 'qr_sessions'

#     id         = db.Column(db.Integer, primary_key=True)
#     token      = db.Column(db.String(64), unique=True, nullable=False,
#                            default=lambda: secrets.token_urlsafe(32))
#     subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
#     teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
#     date       = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)

#     # QR expires after this datetime — teacher controls duration
#     expires_at = db.Column(db.DateTime, nullable=False)
#     is_active  = db.Column(db.Boolean, default=True, nullable=False)
#     created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

#     subject = db.relationship('Subject')
#     teacher = db.relationship('Teacher')

#     @property
#     def is_expired(self):
#         return datetime.utcnow() > self.expires_at

#     @property
#     def is_valid(self):
#         return self.is_active and not self.is_expired

#     def __repr__(self):
#         return f'<QRSession subject={self.subject_id} expires={self.expires_at}>'

#############-------update-----------------
"""
QR SESSION MODEL
================
One row represents a single QR-based attendance window that a teacher opens.

Lifecycle:
  1. Teacher generates QR  → row created, is_active=True
  2. Students scan & submit → Attendance rows created, linked via qr_session_id
  3. Teacher closes session OR expiry_minutes elapses → is_active=False

The token (UUID) is what gets encoded in the QR code URL:
  https://<host>/student/scan?token=<uuid>
"""

import uuid
from datetime import datetime, timedelta
from app import db


class QRSession(db.Model):
    __tablename__ = 'qr_sessions'

    id = db.Column(db.Integer, primary_key=True)

    # UUID token embedded in the QR code URL
    token = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Which subject this session is for
    subject_id = db.Column(
        db.Integer,
        db.ForeignKey('subjects.id'),
        nullable=False,
    )

    # Which teacher generated it
    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey('teachers.id'),
        nullable=False,
    )

    # The date this attendance is being taken for (defaults to today)
    attendance_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    # Window during which students can scan (in minutes)
    expiry_minutes = db.Column(db.Integer, nullable=False, default=15)

    # Teacher can manually deactivate before expiry
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # ------------------------------------------------------------------ #
    #  RELATIONSHIPS
    # ------------------------------------------------------------------ #
    subject = db.relationship('Subject', backref=db.backref('qr_sessions', lazy='dynamic'))
    teacher = db.relationship('Teacher', backref=db.backref('qr_sessions', lazy='dynamic'))

    # ------------------------------------------------------------------ #
    #  HELPER PROPERTIES
    # ------------------------------------------------------------------ #
    @property
    def expires_at(self):
        """Absolute datetime when this session stops accepting scans."""
        return self.created_at + timedelta(minutes=self.expiry_minutes)

    @property
    def is_expired(self):
        """True if the time window has passed."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        """True only if the session is both active AND not yet expired."""
        return self.is_active and not self.is_expired

    @property
    def minutes_remaining(self):
        """How many whole minutes are left (0 if expired)."""
        remaining = (self.expires_at - datetime.utcnow()).total_seconds()
        return max(0, int(remaining // 60))

    def deactivate(self):
        """Manually close the session."""
        self.is_active = False

    def __repr__(self):
        return f'<QRSession {self.token[:8]}… subject={self.subject_id} active={self.is_active}>'