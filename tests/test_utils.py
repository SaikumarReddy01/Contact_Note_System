from app.utils import normalize_note_data

def test_normalize_note_data():
    """Test the note data normalization function."""
    # Test with 'body' field
    assert normalize_note_data({'body': 'test'}) == {'body': 'test'}
    
    # Test with alternative field names
    assert normalize_note_data({'note_body': 'test'}) == {'body': 'test'}
    assert normalize_note_data({'note_text': 'test'}) == {'body': 'test'}
    
    # Test with missing fields
    assert normalize_note_data({'other': 'field'}) == {'body': None}
    
    # Test with empty input
    assert normalize_note_data({}) == {'body': None}