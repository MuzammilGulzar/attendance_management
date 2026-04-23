# # Import all models here so that:
# #   1. SQLAlchemy knows about every table when db.create_all() is called
# #   2. Any file can do:  from app.models import User, Student, Attendance
# #      instead of the longer:  from app.models.user import User

# from app.models.user         import User, Role
# from app.models.department   import Department
# from app.models.teacher      import Teacher, teacher_subjects
# from app.models.student      import Student
# from app.models.subject      import Subject
# from app.models.attendance   import Attendance
# from app.models.notification import Notification
# from app.models.qr_session import QRSession

# # Expose everything at the package level
# __all__ = [
#     'User', 'Role',
#     'Department',
#     'Teacher', 'teacher_subjects',
#     'Student',
#     'Subject',
#     'Attendance',
#     'Notification',
#     'QRSession',
# ]



# Import all models here so that:
#   1. SQLAlchemy knows about every table when db.create_all() is called
#   2. Any file can do:  from app.models import User, Student, Attendance
#      instead of the longer:  from app.models.user import User

from app.models.user         import User, Role
from app.models.department   import Department
from app.models.teacher      import Teacher, teacher_subjects
from app.models.student      import Student
from app.models.subject      import Subject
from app.models.attendance   import Attendance
from app.models.notification import Notification
from app.models.qr_session   import QRSession          # ← ADDED

# Expose everything at the package level
__all__ = [
    'User', 'Role',
    'Department',
    'Teacher', 'teacher_subjects',
    'Student',
    'Subject',
    'Attendance',
    'Notification',
    'QRSession',                                        # ← ADDED
]