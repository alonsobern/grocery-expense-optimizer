from flask import Flask
from app.db import init_db

def create_app():
    """
    Application Factory Function.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    app.secret_key = 'grocery_dev_secret_key_123'
    
    # Initialize the database on startup
    with app.app_context():
        init_db()
    
    # Register the routes blueprint
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
