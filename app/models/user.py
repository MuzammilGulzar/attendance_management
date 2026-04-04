from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


# ============================================================
#  ROLE CONSTANTS
#  Using constants instead of raw strings means if you ever
#  rename a role, you change it in ONE place, not everywhere.
# ============================================================
class Role:
    PRINCIPAL = 'principal'
    HOD       = 'hod'
    TEACHER   = 'teacher'
    STUDENT   = 'student'

    # All valid roles as a list — useful for validation
    ALL = [PRINCIPAL, HOD, TEACHER, STUDENT]


class User(UserMixin, db.Model):
    """
    The central login table.  Every person who can log in has a row here.
    We keep login details (email, password, role) in ONE table, and
    put role-specific details (like semester, department) in separate
    tables (Teacher, Student, etc.).

    Why UserMixin?
      Flask-Login requires 4 properties: is_authenticated, is_active,
      is_anonymous, get_id().  UserMixin provides sensible defaults for
      all four so we don't have to write them ourselves.
    """
    __tablename__ = 'users'

    # ------------------------------------------------------------------ #
    #  PRIMARY KEY
    #  Every table needs a unique identifier per row.
    #  Integer + primary_key=True → auto-increments (1, 2, 3, ...)
    # ------------------------------------------------------------------ #
    id = db.Column(db.Integer, primary_key=True)

    # ------------------------------------------------------------------ #
    #  IDENTITY FIELDS
    # ------------------------------------------------------------------ #
    # unique=True  → two users cannot share the same email
    # nullable=False → every user MUST have an email (can't be empty)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # index=True on first_name/last_name speeds up search queries
    first_name = db.Column(db.String(50), nullable=False)
    last_name  = db.Column(db.String(50), nullable=False)

    # ------------------------------------------------------------------ #
    #  PASSWORD  (we NEVER store the real password — only a hash)
    #  Werkzeug's generate_password_hash turns "mypassword" into a long
    #  random-looking string like "scrypt:32768:8:1$abc123$..."
    #  We can check a password with check_password_hash but CANNOT
    #  reverse the hash back to the original password.
    # ------------------------------------------------------------------ #
    password_hash = db.Column(db.String(256), nullable=False)

    # ------------------------------------------------------------------ #
    #  ROLE  — controls what pages this user can access
    #  Stored as a string: 'principal', 'hod', 'teacher', or 'student'
    # ------------------------------------------------------------------ #
    role = db.Column(db.String(20), nullable=False)

    # ------------------------------------------------------------------ #
    #  STATUS
    #  is_active=False means the account exists but cannot log in.
    #  Used for graduated students and removed staff — we keep the data
    #  but block access.  Flask-Login checks is_active automatically.
    # ------------------------------------------------------------------ #
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # ------------------------------------------------------------------ #
    #  TIMESTAMPS  — always useful to know when a record was created
    #  default=datetime.utcnow  (no parentheses!) means SQLAlchemy calls
    #  this function at the moment a new row is inserted.
    # ------------------------------------------------------------------ #
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # ------------------------------------------------------------------ #
    #  RELATIONSHIPS
    #  These are not database columns — they are Python shortcuts.
    #  user.teacher_profile  → fetches the Teacher row linked to this user
    #  user.student_profile  → fetches the Student row linked to this user
    #  uselist=False means "there is exactly ONE, not a list"
    # ------------------------------------------------------------------ #
    teacher_profile = db.relationship('Teacher', back_populates='user',
                                      uselist=False, cascade='all, delete-orphan')
    student_profile = db.relationship('Student', back_populates='user',
                                      uselist=False, cascade='all, delete-orphan')

    # ------------------------------------------------------------------ #
    #  PASSWORD HELPER METHODS
    # ------------------------------------------------------------------ #
    def set_password(self, password):
        """
        Call this instead of setting password_hash directly.
        Usage:  user.set_password('mypassword123')
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Returns True if the given password matches the stored hash.
        Usage:  if user.check_password(form.password.data): ...
        """
        return check_password_hash(self.password_hash, password)

    # ------------------------------------------------------------------ #
    #  ROLE HELPER PROPERTIES
    #  Instead of writing  user.role == 'hod'  everywhere,
    #  we write  user.is_hod  — cleaner and typo-safe.
    # ------------------------------------------------------------------ #
    @property
    def is_principal(self):
        return self.role == Role.PRINCIPAL

    @property
    def is_hod(self):
        return self.role == Role.HOD

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        # This is what Python prints when you do print(user)
        return f'<User {self.email} [{self.role}]>'