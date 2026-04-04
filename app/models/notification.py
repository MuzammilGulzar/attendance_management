from app import db
from datetime import datetime


class Notification(db.Model):
    """
    In-app notifications sent to users.

    Used for:
      - Alerting a student when their attendance drops below 75%
      - Notifying a teacher when HOD edits their attendance record
      - Informing a student when they are promoted to next semester
      - Confirming to a student when they are graduated

    Design: notifications are stored in DB (not just flash messages)
    so users see them even if they log in later.
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)

    # Who receives this notification
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        nullable=False, index=True)

    # ------------------------------------------------------------------ #
    #  NOTIFICATION TYPE
    #  Used by the template to show different icons/colours per type.
    #  'info'    → blue  — general information
    #  'warning' → amber — attendance low warning
    #  'success' → green — promoted, graduated
    #  'danger'  → red   — critical attendance shortage
    # ------------------------------------------------------------------ #
    type = db.Column(db.String(20), nullable=False, default='info')

    # Short heading shown in notification list
    title   = db.Column(db.String(100), nullable=False)

    # Full message text
    message = db.Column(db.Text, nullable=False)

    # ------------------------------------------------------------------ #
    #  READ TRACKING
    #  is_read=False → shown as unread (bold / highlighted) in the UI
    #  is_read=True  → user has seen it
    #  read_at       → when they opened/dismissed it
    # ------------------------------------------------------------------ #
    is_read = db.Column(db.Boolean,  default=False, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                           nullable=False, index=True)

    # ------------------------------------------------------------------ #
    #  RELATIONSHIP
    # ------------------------------------------------------------------ #
    user = db.relationship('User', backref=db.backref('notifications',
                           lazy='dynamic', order_by='Notification.created_at.desc()'))

    def mark_as_read(self):
        self.is_read = True
        self.read_at = datetime.utcnow()

    def __repr__(self):
        return f'<Notification user={self.user_id} [{self.type}] read={self.is_read}>'