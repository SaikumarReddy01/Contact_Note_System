from flask import jsonify, current_app
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# We'll initialize limiter in create_app, here we just define it
limiter = None

# Initialize rate limiting for the application
def initialize_limiter(app):
    global limiter
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["100 per minute"]
    )
    return limiter

def rate_limit(func):
# Decorator to apply rate limiting to endpoints
    @wraps(func)
    def wrapper(*args, **kwargs):
        # This will use the limiter from the app context
        if limiter:
            return limiter.limit("100 per minute")(func)(*args, **kwargs)
        # If limiter not initialized, just call the function
        return func(*args, **kwargs)
    return wrapper

# Standardize note data format from different input fields
def normalize_note_data(data):
    if not data:
        return {'body': None}
    return {
        'body': data.get('body') or data.get('note_body') or data.get('note_text')
    }

def retry_with_backoff(func):
    from tenacity import retry, stop_after_attempt, wait_exponential
    # Decorator to retry functions with exponential backoff on failure
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper