import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# ======================================================================
#  EXTENSION INSTANCES
#  Created here so models can do:  from app import db
#  NOT connected to any app yet — that happens inside create_app()
#  using the  extension.init_app(app)  pattern.
# ======================================================================
db            = SQLAlchemy()
migrate       = Migrate()
login_manager = LoginManager()


def create_app(config_name=None):
    """
    APPLICATION FACTORY
    -------------------
    Wrapping app creation in a function means:
      1. We can create multiple instances (one for testing, one for running)
      2. No circular imports — extensions are created before the app
      3. All configuration and wiring happens in one clean place
    """

    app = Flask(__name__)

    # ------------------------------------------------------------------ #
    #  LOAD CONFIGURATION
    # ------------------------------------------------------------------ #
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # Normalise: 'production' env may also be signalled by FLASK_ENV='production'
    if config_name not in ('development', 'production'):
        config_name = 'development'

    # Import only the config we actually need
    if config_name == 'production':
        from config.production import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        from config.development import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)

    # ------------------------------------------------------------------ #
    #  CONNECT EXTENSIONS TO THIS APP INSTANCE
    # ------------------------------------------------------------------ #
    db.init_app(app)
    migrate.init_app(app, db)

    # ---- Flask-Login -------------------------------------------------- #
    login_manager.init_app(app)
    login_manager.login_view     = 'auth.login'
    login_manager.login_message  = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # ------------------------------------------------------------------ #
    #  USER LOADER
    #  Flask-Login calls this on every request to fetch the current user
    #  from the database using the ID stored in their session cookie.
    # ------------------------------------------------------------------ #
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        # user_id is always a string from the session — convert to int
        return db.session.get(User, int(user_id))

    # ------------------------------------------------------------------ #
    #  REGISTER BLUEPRINTS
    # ------------------------------------------------------------------ #
    from app.routes.auth      import auth_bp
    from app.routes.principal import principal_bp
    from app.routes.hod       import hod_bp
    from app.routes.teacher   import teacher_bp
    from app.routes.student   import student_bp

    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(principal_bp, url_prefix='/principal')
    app.register_blueprint(hod_bp,       url_prefix='/hod')
    app.register_blueprint(teacher_bp,   url_prefix='/teacher')
    app.register_blueprint(student_bp,   url_prefix='/student')

    # ------------------------------------------------------------------ #
    #  ROOT ROUTE
    # ------------------------------------------------------------------ #
    from flask import redirect, url_for

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    register_error_handlers(app)
    return app


def register_error_handlers(app):
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html', title='Access Denied'), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))