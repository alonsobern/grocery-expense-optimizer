from flask import Flask

def create_app():
    """
    Application Factory Function.
    Creates and configures the Flask application.
    """
    app = Flask(__name__)
    app.secret_key = 'grocery_dev_secret_key_123'
    
    # Register the routes blueprint
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
