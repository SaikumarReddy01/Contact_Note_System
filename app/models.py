from app import db
from datetime import datetime

# Data models for the application:
#User: Stores user credentials and links to their contacts
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    contacts = db.relationship('Contact', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.username}>'
#Contact: Stores contact information with link to owner and notes
class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120))
    notes = db.relationship('Note', backref='contact', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Contact {self.name}>'
#Note: Stores text notes associated with contacts
class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Note {self.id} for Contact {self.contact_id}>'