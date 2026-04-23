# """
# AUTH SERVICE
# ============
# All authentication LOGIC lives here.
# The route file just calls these functions — it never touches the DB directly.

# Why separate?
#   If you later add OAuth or an API, you reuse this service.
#   The route file stays small and readable.
# """

# from app import db
# from app.models.user import User, Role


# def get_user_by_email(email: str):
#     """
#     Fetch a user by their email address.
#     Returns the User object, or None if not found.
#     .lower() ensures emails are case-insensitive.
#     """
#     return User.query.filter_by(email=email.strip().lower()).first()


# def authenticate_user(email: str, password: str):
#     """
#     Verify email + password.

#     Returns a tuple:  (user_or_None, error_message_or_None)

#     Possible outcomes:
#       (user,  None)                  → success
#       (None, 'Invalid email ...')    → email not found
#       (None, 'Incorrect password')   → wrong password
#       (None, 'Account is inactive')  → graduated student or disabled staff
#     """
#     user = get_user_by_email(email)

#     if user is None:
#         # Do NOT say "email not found" — that reveals which emails exist.
#         # A generic message is safer against user enumeration attacks.
#         return None, 'Invalid email or password.'

#     if not user.check_password(password):
#         return None, 'Invalid email or password.'

#     if not user.is_active:
#         return None, ('This account has been deactivated. '
#                       'Graduated students and removed staff cannot log in. '
#                       'Contact the administrator if this is an error.')

#     return user, None


# def get_dashboard_url_for_role(role: str) -> str:
#     """
#     Given a role string, return the URL endpoint to redirect to after login.

#     url_for() is NOT used here because this is the service layer —
#     it has no Flask request context.  The route layer calls url_for()
#     using the string returned here.

#     Returns an endpoint string like 'principal.dashboard'
#     """
#     role_to_endpoint = {
#         Role.PRINCIPAL: 'principal.dashboard',
#         Role.HOD:       'hod.dashboard',
#         Role.TEACHER:   'teacher.dashboard',
#         Role.STUDENT:   'student.dashboard',
#     }
#     # Default to login page if somehow an unknown role exists
#     return role_to_endpoint.get(role, 'auth.login')


# def create_user(email, first_name, last_name, password, role):
#     """
#     Create a new User and save to the database.
#     Used by Principal when adding staff/students.

#     Returns: (new_user, None) on success
#              (None, error_message) on failure
#     """
#     # Check if email already taken
#     if get_user_by_email(email):
#         return None, f'A user with email {email} already exists.'

#     if role not in Role.ALL:
#         return None, f'Invalid role: {role}. Must be one of {Role.ALL}.'

#     user = User(
#         email=email.strip().lower(),
#         first_name=first_name.strip(),
#         last_name=last_name.strip(),
#         role=role
#     )
#     user.set_password(password)

#     db.session.add(user)
#     db.session.commit()
#     return user, None


# def change_password(user, current_password, new_password):
#     """
#     Let a logged-in user change their own password.

#     Returns: (True, None) on success
#              (False, error_message) on failure
#     """
#     if not user.check_password(current_password):
#         return False, 'Current password is incorrect.'

#     if len(new_password) < 8:
#         return False, 'New password must be at least 8 characters.'

#     user.set_password(new_password)
#     db.session.commit()
#     return True, None



"""
AUTH SERVICE
============
All authentication LOGIC lives here.
The route file just calls these functions — it never touches the DB directly.

Why separate?
  If you later add OAuth or an API, you reuse this service.
  The route file stays small and readable.
"""

from app import db
from app.models.user import User, Role


def get_user_by_email(email: str):
    """
    Fetch a user by their email address.
    Returns the User object, or None if not found.
    .lower() ensures emails are case-insensitive.
    """
    # Use ilike for case-insensitive match so emails like
    # 'hod.IT@spcollege.edu' are found even if the user types lowercase.
    return User.query.filter(
        User.email.ilike(email.strip())
    ).first()


def authenticate_user(email: str, password: str):
    """
    Verify email + password.

    Returns a tuple:  (user_or_None, error_message_or_None)

    Possible outcomes:
      (user,  None)                  → success
      (None, 'Invalid email ...')    → email not found
      (None, 'Incorrect password')   → wrong password
      (None, 'Account is inactive')  → graduated student or disabled staff
    """
    user = get_user_by_email(email)

    if user is None:
        # Do NOT say "email not found" — that reveals which emails exist.
        # A generic message is safer against user enumeration attacks.
        return None, 'Invalid email or password.'

    if not user.check_password(password):
        return None, 'Invalid email or password.'

    if not user.is_active:
        return None, ('This account has been deactivated. '
                      'Graduated students and removed staff cannot log in. '
                      'Contact the administrator if this is an error.')

    return user, None


def get_dashboard_url_for_role(role: str) -> str:
    """
    Given a role string, return the URL endpoint to redirect to after login.

    url_for() is NOT used here because this is the service layer —
    it has no Flask request context.  The route layer calls url_for()
    using the string returned here.

    Returns an endpoint string like 'principal.dashboard'
    """
    role_to_endpoint = {
        Role.PRINCIPAL: 'principal.dashboard',
        Role.HOD:       'hod.dashboard',
        Role.TEACHER:   'teacher.dashboard',
        Role.STUDENT:   'student.dashboard',
    }
    # Default to login page if somehow an unknown role exists
    return role_to_endpoint.get(role, 'auth.login')


def create_user(email, first_name, last_name, password, role):
    """
    Create a new User and save to the database.
    Used by Principal when adding staff/students.

    Returns: (new_user, None) on success
             (None, error_message) on failure
    """
    # Check if email already taken
    if get_user_by_email(email):   # ilike check — case-insensitive
        return None, f'A user with email {email} already exists.'

    if role not in Role.ALL:
        return None, f'Invalid role: {role}. Must be one of {Role.ALL}.'

    user = User(
        email=email.strip(),   # store as-is; queries use ilike
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        role=role
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user, None


def change_password(user, current_password, new_password):
    """
    Let a logged-in user change their own password.

    Returns: (True, None) on success
             (False, error_message) on failure
    """
    if not user.check_password(current_password):
        return False, 'Current password is incorrect.'

    if len(new_password) < 8:
        return False, 'New password must be at least 8 characters.'

    user.set_password(new_password)
    db.session.commit()
    return True, None
