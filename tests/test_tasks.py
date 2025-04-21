import pytest
from unittest.mock import patch
from app import celery
from app.tasks import process_note
from app.models import User, Contact, Note
import requests
from unittest.mock import patch, MagicMock

def test_process_note_success(app, database, celery_app, test_user):
    """Test successful note processing"""
    with app.app_context():
        # Create test contact and commit it first to get an ID
        contact = Contact(user_id=test_user.id, name='Test Contact')
        database.session.add(contact)
        database.session.commit()
        
        # Now create the note with the valid contact ID
        note = Note(contact_id=contact.id, body='Test note content')
        database.session.add(note)
        database.session.commit()
        note_id = note.id

    with patch('app.tasks.call_upstream_service') as mock_call:
        mock_call.return_value = {'status': 'received'}
        result = process_note.delay(note_id).get(timeout=5)
        
        assert result['status'] == 'success'
        mock_call.assert_called_once()
        # Verify the correct note was passed to the service
        called_note = mock_call.call_args[0][0]
        assert called_note.id == note_id
        assert called_note.body == 'Test note content'

def test_process_note_retries(app, database, celery_app, test_user):
    """Test retry logic for failed upstream calls"""
    with app.app_context():
        # Ensure test_user is attached to this session
        test_user = database.session.merge(test_user)
        
        # Create test contact and note
        contact = Contact(user_id=test_user.id, name='Retry Contact')
        database.session.add(contact)
        database.session.commit()
        
        note = Note(contact_id=contact.id, body='Retry test note')
        database.session.add(note)
        database.session.commit()
        note_id = note.id
        contact_id = contact.id  # Store contact_id for later use

    with patch('app.tasks.requests.post') as mock_post:
        # Configure mock to fail twice then succeed
        mock_post.side_effect = [
            requests.exceptions.Timeout("First timeout"),
            requests.exceptions.Timeout("Second timeout"),
            MagicMock(
                status_code=200,
                json=lambda: {'status': 'received'},
                raise_for_status=lambda: None
            )
        ]
        
        # Execute task
        result = process_note.delay(note_id)
        
        # Get result with timeout (should succeed after retries)
        try:
            task_result = result.get(timeout=10)
            assert task_result['status'] == 'success'
        except Exception as e:
            pytest.fail(f"Task failed after retries: {str(e)}")
        
        # Verify exactly 3 calls were made
        assert mock_post.call_count == 3
        
        # Verify URL and payload in each call
        expected_url = f'http://127.0.0.1:5000/contacts/{note.contact_id}/notes'
        expected_json = {
            'body': 'Retry test note'
        }
        for call in mock_post.call_args_list:
            args, kwargs = call
            assert args[0] == expected_url  # Check the URL is correct
            assert kwargs['json'] == expected_json
            assert kwargs['timeout'] == 3  # Verify timeout is set

def test_process_note_not_found(app, database, celery_app):
    """Test handling of non-existent notes"""
    with patch('app.tasks.call_upstream_service') as mock_call:
        result = process_note.delay(9999).get(timeout=5)  # Invalid ID
        assert result['status'] == 'error'
        assert 'Note not found' in result['error']
        mock_call.assert_not_called()