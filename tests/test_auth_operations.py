# tests/test_auth_operations.py
from app.models import User
from argon2 import PasswordHasher
ph = PasswordHasher()

def test_user_registration(client, database):
    test_username = "test_user_123"
    test_password = "securepass123"
    
    # 1. Make the registration request
    response = client.post('/auth/register', json={
        'username': test_username,
        'password': test_password
    })
    
    # 2. Check API response
    assert response.status_code == 201
    assert 'user_id' in response.json
    
    # 3. Verify database record
    with database.session() as session:
        user = session.get(User, response.json['user_id'])
        assert user is not None
        assert user.username == test_username
        assert ph.verify(user.password_hash, test_password)  # Verify password hash

def test_user_login(client, test_user):
    response = client.post('/auth/login', json={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_invalid_login(client):
    response = client.post('/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrongpass'
    })
    assert response.status_code == 401