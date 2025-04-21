from app import create_app, make_celery

# Create the Flask app and initialize Celery
flask_app = create_app()
celery = make_celery(flask_app)
