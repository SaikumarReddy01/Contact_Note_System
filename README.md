# Contact Notes API

A robust backend service for managing contacts and their associated notes. This service provides a complete solution with JWT authentication, CRUD operations, and asynchronous processing capabilities.

## Features

- **JWT Authentication**: Secure user authentication and registration with Argon2 password hashing
- **Contact Management**: Full CRUD operations for contacts
- **Notes Management**: Create, read, update, and delete notes attached to contacts
- **Field Normalization**: Handles different input formats for note data (`body`, `note_body`, `note_text`)
- **Rate Limiting**: Prevents abuse with configurable rate limits
- **Background Processing**: Uses Celery to handle note processing asynchronously
- **Retry Mechanism**: Implements exponential backoff for external service calls
- **Error Handling**: Graceful error handling with proper status codes
- **API Documentation**: Interactive Swagger UI for API exploration

## Technology Stack

- **Flask**: Web framework for building the API
- **SQLAlchemy**: ORM for database operations
- **Flask-JWT-Extended**: JWT authentication and token management
- **Redis**: For token blacklisting and Celery task queue
- **Celery**: For asynchronous task processing
- **Argon2**: Modern, secure password hashing algorithm
- **Swagger UI**: For interactive API documentation

## Setup Instructions

### Prerequisites

- Python 3.8+
- Redis server
- SQLite (development) or PostgreSQL (production)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd contact-notes-api
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the following environment variables:
   ```
   FLASK_ENV=development
   DATABASE_URL=sqlite:///dev.db
   JWT_SECRET_KEY=your-secret-key (eg:3f9f2d8e9c7b4a1d5f6e4c3b2a0e9d8c)
   REDIS_URL=redis://localhost:6379/0
   RATE_LIMIT=100/minute
   ```

### Database Setup

Initialize the database:
```bash
flask db upgrade
```

### Running the Application

1. Start Redis server:
   ```bash
   redis-server
   ```

2. Start the Flask application:
   ```bash
   python run.py
   ```

3. Start the Celery worker in a separate terminal:
   ```bash
   celery -A celery_worker.celery worker --loglevel=info
   ```

4. Access the Swagger UI documentation at:
   ```
   http://localhost:5000/swagger-ui/
   ```

## API Usage

The API is documented with Swagger UI, accessible at `/swagger-ui/` when the application is running.

### Authentication Flow

1. Register a new user:
   ```bash
   curl -X POST http://localhost:5000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username": "user", "password": "password"}'
   ```

2. Login to get a JWT token:
   ```bash
   curl -X POST http://localhost:5000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "user", "password": "password"}'
   ```

3. Use the token in subsequent requests:
   ```bash
   curl -X GET http://localhost:5000/contacts \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

4. Logout to invalidate the token:
   ```bash
   curl -X POST http://localhost:5000/auth/logout \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## Testing

The project includes comprehensive test coverage. Run the tests with:

```bash
pytest
```

Key test modules:
- `test_auth_operations.py`: Authentication flow tests
- `test_contact_operations.py`: Contact CRUD operation tests
- `test_note_operations.py`: Note CRUD operation tests
- `test_tasks.py`: Asynchronous task processing tests
- `test_utils.py`: Utility function tests

## Key Design Decisions

### Architecture

- **Blueprint-based Structure**: Organized routes into logical groups
- **Factory Pattern**: Used application factory pattern for flexible configuration
- **Model-View Separation**: Clean separation between data models and controllers

### Security

- **Argon2 Password Hashing**: Modern, secure password hashing algorithm
- **JWT Token Blacklisting**: Prevents use of logged-out tokens
- **Rate Limiting**: Protects against brute force and DoS attacks
- **Security Headers**: Added defensive HTTP headers

### Scalability

- **Asynchronous Processing**: Decoupled note creation from processing using Celery
- **Retry Mechanism**: Implements exponential backoff for external service calls
- **Configurable Environment Settings**: Different configurations for development, testing, and production

## Future Improvements

- Add pagination for listing endpoints
- Implement refresh tokens for better security
- Add more comprehensive test coverage
- Add user profile management
- Implement contact search functionality
- Add more sophisticated rate limiting strategies
- Implement data validation with Marshmallow or Pydantic
- Add Docker containerization for easier deployment
