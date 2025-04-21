# tests/conftest.py
import pytest
from app import create_app, db as _db
from app.models import User, Contact, Note
from werkzeug.security import generate_password_hash
from datetime import datetime
from argon2 import PasswordHasher
import pytest
from app import create_app, db as _db, celery

ph = PasswordHasher()

@pytest.fixture(scope='function')
def app():
    app = create_app('app.config.TestingConfig')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key',
        'RATE_LIMIT': '200/minute'
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function')
def database(app):
    """Setup database for tests."""
    return _db

@pytest.fixture(scope='function')
def test_user(app, database):
    """Create a test user."""
    user = User(
        username='testuser',
        password_hash=ph.hash('testpass')
    )
    database.session.add(user)
    database.session.commit()
    return user

@pytest.fixture(scope='function')
def auth_headers(app, client, test_user):
    """Generate authentication headers with valid JWT token."""
    # Login and get token
    response = client.post(
        '/auth/login',
        json={'username': 'testuser', 'password': 'testpass'}
    )
    data = response.get_json()
    return {'Authorization': f'Bearer {data["access_token"]}'}

@pytest.fixture(scope='function')
def test_contact(app, database, test_user):
    """Create a test contact."""
    contact = Contact(
        user_id=test_user.id,
        name='Test Contact',
        email='test@example.com'
    )
    database.session.add(contact)
    database.session.commit()
    return contact

@pytest.fixture(scope='function')
def test_note(app, database, test_contact):
    """Create a test note."""
    note = Note(
        contact_id=test_contact.id,
        body='Test note',
        created_at=datetime.utcnow()
    )
    database.session.add(note)
    database.session.commit()
    return note
@pytest.fixture(autouse=True)
def setup_celery(celery_app):
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    
@pytest.fixture(scope='function')
def celery_app(app):
    """Fixture to configure Celery for testing"""
    # Make sure tasks are imported and registered
    from app.tasks import process_note
    
    # Configure Celery to run tasks synchronously
    celery.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        imports=('app.tasks',) 
    )
    return celery