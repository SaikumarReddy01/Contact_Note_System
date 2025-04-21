from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Contact, Note, db
from app.utils import normalize_note_data, rate_limit
from app.tasks import process_note, call_upstream_service  # Import the shared function
from flask import current_app as app

notes_bp = Blueprint('notes', __name__, url_prefix='/contacts/<int:contact_id>/notes')

# Create a new note for a specific contact and queue for background processing
@notes_bp.route('', methods=['POST'])
@jwt_required()
@rate_limit
def create_note(contact_id):
    try:
        current_user_id = get_jwt_identity()
        contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
        
        if not contact:
            return jsonify({'error': 'Contact not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Enhanced normalization
        body = data.get('body') or data.get('note_body') or data.get('note_text')
        if not body:
            return jsonify({'error': 'Note content is required'}), 400

        new_note = Note(
            contact_id=contact_id,
            body=body
        )
        
        db.session.add(new_note)
        db.session.commit()
        
        # Add error handling for Celery task
        try:
            process_note.delay(new_note.id)
        except Exception as e:
            app.logger.error(f"Failed to queue Celery task: {str(e)}")
            # Continue even if Celery fails - this might be what you want
        
        return jsonify({
            'id': new_note.id,
            'body': new_note.body,
            'created_at': new_note.created_at.isoformat()
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Note creation failed: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
# Retrieve all notes for a specific contact
@notes_bp.route('', methods=['GET'])
@jwt_required()
@rate_limit
def get_all_notes(contact_id):
    current_user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    notes = Note.query.filter_by(contact_id=contact_id).all()
    
    return jsonify([{
        'id': note.id,
        'body': note.body,
        'created_at': note.created_at.isoformat()
    } for note in notes]), 200

# Retrieve a specific note by ID for a given contact
@notes_bp.route('/<int:note_id>', methods=['GET'])
@jwt_required()
@rate_limit
def get_single_note(contact_id, note_id):
    current_user_id = get_jwt_identity()
    note = Note.query.join(Contact).filter(
        Note.id == note_id,
        Contact.id == contact_id,
        Contact.user_id == current_user_id
    ).first()
    
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    
    return jsonify({
        'id': note.id,
        'body': note.body,
        'created_at': note.created_at.isoformat()
    }), 200

# Update an existing note's content
@notes_bp.route('/<int:note_id>', methods=['PUT'])
@jwt_required()
@rate_limit
def update_note(contact_id, note_id):
    current_user_id = get_jwt_identity()
    note = Note.query.join(Contact).filter(
        Note.id == note_id,
        Contact.id == contact_id,
        Contact.user_id == current_user_id
    ).first()
    
    if not note:
        return jsonify({'error': 'Note not found'}), 404

    data = normalize_note_data(request.get_json())
    if not data.get('body'):
        return jsonify({'error': 'Note body is required'}), 400
    
    note.body = data['body']
    db.session.commit()
    
    return jsonify({
        'id': note.id,
        'body': note.body,
        'created_at': note.created_at.isoformat()
    }), 200

# Delete a specific note from a contact
@notes_bp.route('/<int:note_id>', methods=['DELETE'])
@jwt_required()
@rate_limit
def delete_note(contact_id, note_id):
    current_user_id = get_jwt_identity()
    note = Note.query.join(Contact).filter(
        Note.id == note_id,
        Contact.id == contact_id,
        Contact.user_id == current_user_id
    ).first()
    
    if not note:
        return jsonify({'error': 'Note not found'}), 404
    
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({'message': 'Note deleted successfully'}), 200