from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from flask import jsonify
from celery import Celery
from flask_swagger_ui import get_swaggerui_blueprint
import json

# Load environment variables
load_dotenv()

# Initialize extensions without app
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

# Configure Redis URL - use environment variables or fallback to default
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Create Celery instance
celery = Celery(__name__,
               broker=REDIS_URL,
               backend=REDIS_URL,
               include=['app.tasks'])

# Configure Celery instance with Flask app context for database access
def make_celery(app=None):
    if app:
        celery.conf.update(
            broker_url=app.config.get('CELERY_BROKER_URL', REDIS_URL),
            result_backend=app.config.get('CELERY_RESULT_BACKEND', REDIS_URL)
        )
        celery.conf.update(app.config)

        class ContextTask(celery.Task):
            abstract = True  # Marks this as a base class, not a task to be registered
            
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask
    return celery

# Flask application factory that initializes app with extensions and blueprints
def create_app(config_class=None):
    app = Flask(__name__)
    
    from app.utils import initialize_limiter
    limiter = initialize_limiter(app)
    # Determine which config to load
    if config_class is None:
        env = os.getenv('FLASK_ENV', 'development')
        if env == 'production':
            app.config.from_object('app.config.ProductionConfig')
        elif env == 'testing':
            app.config.from_object('app.config.TestingConfig')
        else:
            app.config.from_object('app.config.DevelopmentConfig')
    else:
        app.config.from_object(config_class)

    if 'CELERY_BROKER_URL' not in app.config:
        app.config['CELERY_BROKER_URL'] = REDIS_URL
    if 'CELERY_RESULT_BACKEND' not in app.config:
        app.config['CELERY_RESULT_BACKEND'] = REDIS_URL

    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Update Celery config with app - make sure to call make_celery!
    make_celery(app)

    # Register blueprints
    from app.auth import auth_bp
    from app.contacts import contacts_bp
    from app.notes import notes_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(contacts_bp)
    app.register_blueprint(notes_bp)
    
    # Set up Swagger docs
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.json'

    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Contact Notes API"
        }
    )

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    # Create a route to serve the swagger.json file
    @app.route('/static/swagger.json')
    def get_swagger():
        try:
            with open('app/static/swagger.json', 'r') as f:
                return jsonify(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            app.logger.error(f"Error loading swagger file: {str(e)}")
            return jsonify({"error": "Swagger file not available"}), 500

    # Global error handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"Unhandled exception: {str(e)}")
        return jsonify({
            "error": "An unexpected error occurred",
            "detail": str(e) if app.debug else None
        }), 500
    @app.route("/")
    def root():
        return jsonify({"message": "Server is running!"})

    return app
