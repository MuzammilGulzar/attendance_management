import os
from app import create_app

# Create the app using the environment setting
# Set FLASK_ENV=production in your server environment for production
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # This block only runs when you execute:  python run.py
    # It does NOT run when a production server (like gunicorn) imports this file.
    # debug=True  →  auto-reloads on code change, shows detailed error pages
    # host='0.0.0.0' → accessible from other devices on the same network
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000
    )