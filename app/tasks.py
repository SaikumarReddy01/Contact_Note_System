from app import celery, db
from app.models import Note
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)
#Note processing queue
@celery.task
def process_note(note_id):
    """
    Process a note in the background.
    This could include analytics, enrichment, or pushing to external services.
    """
    # Context is handled by the ContextTask class in __init__.py
    note = Note.query.get(note_id)
    if note:
        try:
            # Call the upstream service with retry
            call_upstream_service(note)
            # Update the note to mark as processed if needed
            # note.processed = True
            # db.session.commit()
            return {"status": "success", "note_id": note_id}
        except Exception as e:
            logger.error(f"Error processing note {note_id}: {str(e)}")
            return {"status": "error", "note_id": note_id, "error": str(e)}
    return {"status": "error", "note_id": note_id, "error": "Note not found"}
#External service call with retry mechanism
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_upstream_service(note):
    """
    Call an external service with retry capability.
    """
    try:
        # Simulate calling an external service
        response = requests.post(
            'http://127.0.0.1:5000/notes',
            json={
                'note_id': note.id,
                'body': note.body
            },
            timeout=3  # Set a reasonable timeout
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        logger.warning(f"Upstream service timeout for note {note.id}")
        raise Exception("Service temporarily unavailable")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling upstream service: {str(e)}")
        raise