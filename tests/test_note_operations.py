# tests/test_note_operations.py
import pytest
from app.models import Note
from unittest.mock import patch

def test_create_note(client, auth_headers, test_contact):
    """Test note creation."""
    response = client.post(f'/contacts/{test_contact.id}/notes', json={
        'body': 'New test note'
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['body'] == 'New test note'

def test_get_all_notes(client, auth_headers, test_contact, test_note):
    """Test retrieving all notes for a contact."""
    response = client.get(f'/contacts/{test_contact.id}/notes', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['body'] == 'Test note'

def test_get_single_note(client, auth_headers, test_contact, test_note):
    """Test retrieving a single note."""
    response = client.get(f'/contacts/{test_contact.id}/notes/{test_note.id}', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['body'] == 'Test note'

def test_update_note(client, auth_headers, test_contact, test_note):
    """Test updating a note."""
    response = client.put(f'/contacts/{test_contact.id}/notes/{test_note.id}', json={
        'body': 'Updated note'
    }, headers=auth_headers)
    assert response.status_code == 200
    from app import db
    # Reload the note from database
    updated_note = db.session.get(Note, test_note.id)
    assert updated_note.body == 'Updated note'

def test_delete_note(client, auth_headers, test_contact, test_note):
    """Test deleting a note."""
    response = client.delete(f'/contacts/{test_contact.id}/notes/{test_note.id}', headers=auth_headers)
    assert response.status_code == 200
    from app import db
    # Check that the note doesn't exist anymore
    deleted_note = db.session.get(Note, test_note.id)
    assert deleted_note is None
def test_create_note_triggers_task(client, auth_headers, test_contact, celery_app):
    with patch('app.tasks.process_note.delay') as mock_task:
        response = client.post(
            f'/contacts/{test_contact.id}/notes',
            json={'body': 'Test'},
            headers=auth_headers
        )
        assert response.status_code == 201
        note_id = response.json['id']
        mock_task.assert_called_once_with(note_id)  