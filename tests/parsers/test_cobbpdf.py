import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from pathlib import Path
from pdfminer.pdfparser import PDFSyntaxError

from parsers.cobbpdf import CobbPDFParser
from parsers.exceptions import ValidationError, DataFormatError, DatabaseError

@pytest.fixture
def mock_db_connection():
    connection = Mock()
    connection.commit = Mock()
    connection.rollback = Mock()
    connection.execute = Mock()
    return connection

@pytest.fixture
def parser(mock_db_connection):
    return CobbPDFParser(connection=mock_db_connection)

@pytest.fixture
def sample_pdf_text():
    return """
    Property ID: 12-3456-78-901
    Location Address: 123 Main St, Marietta, GA 30060
    District: 16
    Land Lot: 1234
    Tax Amount: $1,234.56
    Assessment Date: 2024-01-15
    """

def test_parse_valid_pdf(parser, sample_pdf_text):
    with patch('parsers.cobbpdf.extract_text') as mock_extract:
        mock_extract.return_value = sample_pdf_text
        
        result = parser.parse("dummy.pdf")
        
        assert result['property_id'] == '12-3456-78-901'
        assert result['location_address'] == '123 Main St, Marietta, GA 30060'
        assert result['district'] == '16'
        assert result['land_lot'] == '1234'
        assert result['tax_amount'] == 1234.56
        assert result['assessment_date'] == '2024-01-15'

def test_validate_valid_data(parser):
    valid_data = {
        'property_id': '12-3456-78-901',
        'location_address': '123 Main St',
        'district': '16',
        'land_lot': '1234',
        'tax_amount': 1234.56,
        'assessment_date': '2024-01-15'
    }
    
    assert parser.validate(valid_data) is True

@pytest.mark.parametrize("invalid_field,invalid_value", [
    ('property_id', '123-456'),  # Wrong format
    ('tax_amount', -100),        # Negative amount
    ('assessment_date', 'invalid-date')  # Wrong date format
])
def test_validate_invalid_data(parser, invalid_field, invalid_value):
    valid_data = {
        'property_id': '12-3456-78-901',
        'location_address': '123 Main St',
        'district': '16',
        'land_lot': '1234',
        'tax_amount': 1234.56,
        'assessment_date': '2024-01-15'
    }
    valid_data[invalid_field] = invalid_value
    
    with pytest.raises(ValidationError):
        parser.validate(valid_data)

def test_save_valid_data(parser, mock_db_connection):
    valid_data = {
        'property_id': '12-3456-78-901',
        'location_address': '123 Main St',
        'district': '16',
        'land_lot': '1234',
        'tax_amount': 1234.56,
        'assessment_date': '2024-01-15'
    }
    
    parser.save(valid_data)
    
    mock_db_connection.execute.assert_called_once()
    mock_db_connection.commit.assert_called_once()

def test_save_database_error(parser, mock_db_connection):
    mock_db_connection.execute.side_effect = Exception("Database error")
    
    with pytest.raises(DatabaseError):
        parser.save({
            'property_id': '12-3456-78-901',
            'location_address': '123 Main St',
            'district': '16',
            'land_lot': '1234',
            'tax_amount': 1234.56,
            'assessment_date': '2024-01-15'
        })
    
    mock_db_connection.rollback.assert_called_once()

def test_parse_invalid_pdf(parser):
    with patch('parsers.cobbpdf.extract_text') as mock_extract:
        mock_extract.side_effect = PDFSyntaxError("Invalid PDF")
        
        with pytest.raises(DataFormatError):
            parser.parse("invalid.pdf")

def test_clean(parser):
    parser.data = {'some': 'data'}
    parser.clean()
    assert parser.data == {}
