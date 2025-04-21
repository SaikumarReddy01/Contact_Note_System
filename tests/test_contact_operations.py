from app.models import Contact, Note, User

def test_create_contact(client, auth_headers, test_user):
    """Test contact creation."""
    response = client.post('/contacts', json={
        'name': 'New Contact',
        'email': 'new@example.com'
    }, headers=auth_headers)
    assert response.status_code == 201
    assert Contact.query.filter_by(user_id=test_user.id, name='New Contact').first() is not None

def test_get_all_contacts(client, auth_headers, test_contact):
    # This should only see the test_contact created in this test
    response = client.get('/contacts', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json) == 1  # Only the fixture contact

def test_get_single_contact(client, auth_headers, test_contact):
    """Test retrieving a single contact."""
    response = client.get(f'/contacts/{test_contact.id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['name'] == 'Test Contact'

def test_update_contact(client, auth_headers, test_contact):
    """Test updating a contact."""
    response = client.put(f'/contacts/{test_contact.id}', json={
        'name': 'Updated Contact'
    }, headers=auth_headers)
    assert response.status_code == 200
    assert Contact.query.get(test_contact.id).name == 'Updated Contact'

def test_delete_contact(client, auth_headers, test_contact):
    """Test deleting a contact."""
    response = client.delete(f'/contacts/{test_contact.id}', headers=auth_headers)
    assert response.status_code == 200
    assert Contact.query.get(test_contact.id) is None