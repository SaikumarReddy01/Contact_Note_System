from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Contact, db
from app.utils import rate_limit

contacts_bp = Blueprint('contacts', __name__, url_prefix='/contacts')

# Create a new contact for the authenticated user
@contacts_bp.route('', methods=['POST'])
@jwt_required()
@rate_limit
def create_contact():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400

    new_contact = Contact(
        user_id=current_user_id,
        name=data['name'],
        email=data.get('email')
    )
    
    db.session.add(new_contact)
    db.session.commit()
    
    return jsonify({
        'id': new_contact.id,
        'name': new_contact.name,
        'email': new_contact.email
    }), 201

# Retrieve all contacts for the authenticated user
@contacts_bp.route('', methods=['GET'])
@jwt_required()
@rate_limit
def get_all_contacts():
    current_user_id = get_jwt_identity()
    contacts = Contact.query.filter_by(user_id=current_user_id).all()
    
    return jsonify([{
        'id': contact.id,
        'name': contact.name,
        'email': contact.email
    } for contact in contacts]), 200

# Retrieve a specific contact by ID for the authenticated user
@contacts_bp.route('/<int:contact_id>', methods=['GET'])
@jwt_required()
@rate_limit
def get_single_contact(contact_id):
    current_user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    return jsonify({
        'id': contact.id,
        'name': contact.name,
        'email': contact.email
    }), 200
# Update an existing contact's information
@contacts_bp.route('/<int:contact_id>', methods=['PUT'])
@jwt_required()
@rate_limit
def update_contact(contact_id):
    current_user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404

    data = request.get_json()
    if 'name' in data:
        contact.name = data['name']
    if 'email' in data:
        contact.email = data['email']
    
    db.session.commit()
    
    return jsonify({
        'id': contact.id,
        'name': contact.name,
        'email': contact.email
    }), 200
    
# Delete a contact and all associated notes
@contacts_bp.route('/<int:contact_id>', methods=['DELETE'])
@jwt_required()
@rate_limit
def delete_contact(contact_id):
    current_user_id = get_jwt_identity()
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user_id).first()
    
    if not contact:
        return jsonify({'error': 'Contact not found'}), 404
    
    db.session.delete(contact)
    db.session.commit()
    
    return jsonify({'message': 'Contact deleted successfully'}), 200