from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, Contact, Note

# Standardize note data format from different input fields
def normalize_note_data(data):
    return {
        'body': data.get('body') or data.get('note_body') or data.get('note_text')
    }

# Retrieve all contacts for the authenticated user
@app.route('/contacts', methods=['GET'])
@jwt_required()
def get_contacts():
    current_user_id = get_jwt_identity()
    contacts = Contact.query.filter_by(user_id=current_user_id).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'email': c.email
    } for c in contacts]), 200

# Retrieve a specific contact by ID
@app.route('/contacts/<int:contact_id>', methods=['GET'])
@jwt_required()
def get_contact(contact_id):
    current_user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    return jsonify({
        'id': contact.id,
        'name': contact.name,
        'email': contact.email
    }), 200
# Update an existing contact's information
@app.route('/contacts/<int:contact_id>', methods=['PUT'])
@jwt_required()
def update_contact(contact_id):
    current_user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    
    data = request.get_json()
    if 'name' in data:
        contact.name = data['name']
    if 'email' in data:
        contact.email = data['email']
    
    db.session.commit()
    return jsonify({"message": "Contact updated"}), 200
    
# Delete a contact and all associated notes
@app.route('/contacts/<int:contact_id>', methods=['DELETE'])
@jwt_required()
def delete_contact(contact_id):
    current_user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    
    db.session.delete(contact)
    db.session.commit()
    return jsonify({"message": "Contact deleted"}), 200

# Create a new note for a specific contact
@app.route('/contacts/<int:contact_id>/notes', methods=['POST'])
@jwt_required()
def create_note(contact_id):
    current_user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
    if not contact:
        return jsonify({"error": "Contact not found"}), 404

    data = normalize_note_data(request.get_json())
    if not data.get('body'):
        return jsonify({"error": "Note body is required"}), 400
    
    new_note = Note(contact_id=contact_id, body=data['body'])
    db.session.add(new_note)
    db.session.commit()
    return jsonify({
        'id': new_note.id,
        'body': new_note.body,
        'created_at': new_note.created_at.isoformat()
    }), 201

# Retrieve all notes for a specific contact
@app.route('/contacts/<int:contact_id>/notes', methods=['GET'])
@jwt_required()
def get_notes(contact_id):
    current_user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    
    notes = Note.query.filter_by(contact_id=contact_id).all()
    return jsonify([{
        'id': n.id,
        'body': n.body,
        'created_at': n.created_at.isoformat()
    } for n in notes]), 200

# Update an existing note's content
@app.route('/contacts/<int:contact_id>/notes/<int:note_id>', methods=['PUT'])
@jwt_required()
def update_note(contact_id, note_id):
    current_user_id = get_jwt_identity()
    note = Note.query.join(Contact).filter(
        Note.id == note_id,
        Contact.id == contact_id,
        Contact.user_id == current_user_id
    ).first()
    
    if not note:
        return jsonify({"error": "Note not found"}), 404
    
    data = normalize_note_data(request.get_json())
    if not data.get('body'):
        return jsonify({"error": "Note body is required"}), 400
    
    note.body = data['body']
    db.session.commit()
    return jsonify({"message": "Note updated"}), 200

# Delete a specific note from a contact
@app.route('/contacts/<int:contact_id>/notes/<int:note_id>', methods=['DELETE'])
@jwt_required()
def delete_note(contact_id, note_id):
    current_user_id = get_jwt_identity()
    note = Note.query.join(Contact).filter(
        Note.id == note_id,
        Contact.id == contact_id,
        Contact.user_id == current_user_id
    ).first()
    
    if not note:
        return jsonify({"error": "Note not found"}), 404
    
    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": "Note deleted"}), 200