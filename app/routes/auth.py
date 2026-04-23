# """
# AUTH ROUTES  (Controller layer)
# ================================
# These functions handle HTTP requests.  They:
#   1. Read form data
#   2. Call the service layer to do the actual work
#   3. Redirect or render a template based on the result

# They do NOT contain business logic — that lives in auth_service.py.
# """

# from flask import (Blueprint, render_template, redirect,
#                    url_for, flash, request)
# from flask_login import login_user, logout_user, login_required, current_user

# from app.forms.auth_forms import LoginForm, ChangePasswordForm
# from app.services.auth_service import (authenticate_user,
#                                         get_dashboard_url_for_role,
#                                         change_password)

# # ------------------------------------------------------------------ #
# #  BLUEPRINT DEFINITION
# #  name='auth'        → used in url_for('auth.login')
# #  url_prefix='/auth' → set in app/__init__.py
# # ------------------------------------------------------------------ #
# auth_bp = Blueprint('auth', __name__)


# # ------------------------------------------------------------------ #
# #  LOGIN
# # ------------------------------------------------------------------ #
# @auth_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     """
#     GET  → show the login form
#     POST → validate credentials, log in, redirect to role dashboard

#     If user is already logged in, skip the form and redirect directly.
#     """
#     # Already logged in? Send them to their dashboard
#     if current_user.is_authenticated:
#         return _redirect_to_dashboard(current_user.role)

#     form = LoginForm()

#     # form.validate_on_submit() returns True only when:
#     #   - The request is a POST (form was submitted)
#     #   - All validators pass (email format, required fields, CSRF token)
#     if form.validate_on_submit():

#         # --- Ask the service layer to verify credentials ---
#         user, error = authenticate_user(
#             email=form.email.data,
#             password=form.password.data
#         )

#         if error:
#             # Authentication failed — show error, stay on login page
#             flash(error, 'danger')
#             return render_template('auth/login.html', form=form, title='Login')

#         # --- Success: log the user in ---
#         # login_user() sets the session cookie in the user's browser.
#         # remember=True → cookie survives browser close (30 days by default)
#         login_user(user, remember=form.remember.data)

#         # --- Redirect to the page they originally tried to visit ---
#         # If someone tried to visit /hod/dashboard without logging in,
#         # Flask-Login saves that URL in 'next' and we redirect there after login.
#         # We MUST validate 'next' to prevent open-redirect attacks.
#         next_page = request.args.get('next')
#         # next_page = request.form.get('next') or request.args.get('next')
#         if next_page and next_page.startswith('/'):
#             # Only allow relative URLs (starting with /) — never external URLs
#             return redirect(next_page)

#         flash(f'Welcome back, {user.first_name}!', 'success')
#         return _redirect_to_dashboard(user.role)

#     # GET request — just show the form
#     return render_template('auth/login.html', form=form, title='Login')


# # ------------------------------------------------------------------ #
# #  LOGOUT
# # ------------------------------------------------------------------ #
# @auth_bp.route('/logout')
# @login_required   # Can't log out if you're not logged in
# def logout():
#     """
#     Clears the session cookie from the user's browser.
#     After this, current_user becomes the anonymous user.
#     """
#     name = current_user.first_name  # save before clearing session
#     logout_user()
#     flash(f'You have been logged out, {name}. See you soon!', 'info')
#     return redirect(url_for('auth.login'))


# # ------------------------------------------------------------------ #
# #  CHANGE PASSWORD
# # ------------------------------------------------------------------ #
# @auth_bp.route('/change-password', methods=['GET', 'POST'])
# @login_required
# def change_password_view():
#     """Any logged-in user can change their own password."""
#     form = ChangePasswordForm()

#     if form.validate_on_submit():
#         success, error = change_password(
#             user=current_user,
#             current_password=form.current_password.data,
#             new_password=form.new_password.data
#         )
#         if success:
#             flash('Password changed successfully!', 'success')
#             return _redirect_to_dashboard(current_user.role)
#         else:
#             flash(error, 'danger')

#     return render_template('auth/change_password.html',
#                            form=form, title='Change Password')


# # ------------------------------------------------------------------ #
# #  HELPER — keeps redirect logic in one place
# # ------------------------------------------------------------------ #
# def _redirect_to_dashboard(role: str):
#     """
#     Internal helper function (starts with _ = private convention).
#     Converts a role string to the correct dashboard URL and redirects.
#     """
#     endpoint = get_dashboard_url_for_role(role)
#     return redirect(url_for(endpoint))

##########3--------update------------
"""
AUTH ROUTES  (Controller layer)
================================
These functions handle HTTP requests.  They:
  1. Read form data
  2. Call the service layer to do the actual work
  3. Redirect or render a template based on the result

They do NOT contain business logic — that lives in auth_service.py.
"""

from urllib.parse import urlparse                          # ← ADDED

from flask import (Blueprint, render_template, redirect,
                   url_for, flash, request)
from flask_login import login_user, logout_user, login_required, current_user

from app.forms.auth_forms import LoginForm, ChangePasswordForm
from app.services.auth_service import (authenticate_user,
                                        get_dashboard_url_for_role,
                                        change_password)

# ------------------------------------------------------------------ #
#  BLUEPRINT DEFINITION
#  name='auth'        → used in url_for('auth.login')
#  url_prefix='/auth' → set in app/__init__.py
# ------------------------------------------------------------------ #
auth_bp = Blueprint('auth', __name__)


# ------------------------------------------------------------------ #
#  LOGIN
# ------------------------------------------------------------------ #
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    GET  → show the login form
    POST → validate credentials, log in, redirect to role dashboard

    If user is already logged in, skip the form and redirect directly.
    """
    # Already logged in? Send them to their dashboard
    if current_user.is_authenticated:
        return _redirect_to_dashboard(current_user.role)

    form = LoginForm()

    # form.validate_on_submit() returns True only when:
    #   - The request is a POST (form was submitted)
    #   - All validators pass (email format, required fields, CSRF token)
    if form.validate_on_submit():

        # --- Ask the service layer to verify credentials ---
        user, error = authenticate_user(
            email=form.email.data,
            password=form.password.data
        )

        if error:
            # Authentication failed — show error, stay on login page
            flash(error, 'danger')
            return render_template('auth/login.html', form=form, title='Login')

        # --- Success: log the user in ---
        # login_user() sets the session cookie in the user's browser.
        # remember=True → cookie survives browser close (30 days by default)
        login_user(user, remember=form.remember.data)

        # --- Redirect to the page they originally tried to visit ---
        # When a student scans a QR code while logged out, Flask-Login saves
        # the scan URL in 'next' so we return them there after login.
        #
        # FIX: Mobile browsers and QR scanners may produce an absolute URL
        # (e.g. http://192.168.1.10:5000/student/scan?token=...) rather than
        # a relative path.  The old check `next_page.startswith('/')` rejected
        # those, silently dropping the student back to the dashboard instead of
        # completing the attendance scan.
        #
        # New logic: allow relative URLs *and* absolute URLs that point to
        # the same host — reject only genuinely external redirects.
        next_page = request.args.get('next')
        if next_page:
            parsed = urlparse(next_page)
            # parsed.netloc is empty for relative URLs like /student/scan?token=...
            # For absolute URLs like http://192.168.x.x:5000/student/scan?token=...
            # we compare the netloc against the current request host.
            is_safe = (not parsed.netloc) or (parsed.netloc == request.host)
            if is_safe:
                return redirect(next_page)

        flash(f'Welcome back, {user.first_name}!', 'success')
        return _redirect_to_dashboard(user.role)

    # GET request — just show the form
    return render_template('auth/login.html', form=form, title='Login')


# ------------------------------------------------------------------ #
#  LOGOUT
# ------------------------------------------------------------------ #
@auth_bp.route('/logout')
@login_required   # Can't log out if you're not logged in
def logout():
    """
    Clears the session cookie from the user's browser.
    After this, current_user becomes the anonymous user.
    """
    name = current_user.first_name  # save before clearing session
    logout_user()
    flash(f'You have been logged out, {name}. See you soon!', 'info')
    return redirect(url_for('auth.login'))


# ------------------------------------------------------------------ #
#  CHANGE PASSWORD
# ------------------------------------------------------------------ #
@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password_view():
    """Any logged-in user can change their own password."""
    form = ChangePasswordForm()

    if form.validate_on_submit():
        success, error = change_password(
            user=current_user,
            current_password=form.current_password.data,
            new_password=form.new_password.data
        )
        if success:
            flash('Password changed successfully!', 'success')
            return _redirect_to_dashboard(current_user.role)
        else:
            flash(error, 'danger')

    return render_template('auth/change_password.html',
                           form=form, title='Change Password')


# ------------------------------------------------------------------ #
#  HELPER — keeps redirect logic in one place
# ------------------------------------------------------------------ #
def _redirect_to_dashboard(role: str):
    """
    Internal helper function (starts with _ = private convention).
    Converts a role string to the correct dashboard URL and redirects.
    """
    endpoint = get_dashboard_url_for_role(role)
    return redirect(url_for(endpoint))