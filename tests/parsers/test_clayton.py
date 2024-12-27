import unittest
from unittest.mock import Mock, patch
import pandas as pd
import tempfile
import os
from pathlib import Path

from parsers.clayton import ClaytonPDFParser, ClaytonExcelParser
from parsers.exceptions import ValidationError, DataFormatError
from parsers.utils.db import DatabaseConnection

class TestClaytonPDFParser(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=DatabaseConnection)
        self.parser = ClaytonPDFParser(connection=self.mock_db)
        
        # Sample PDF content
        self.pdf_content = """
        Tax Assessment Notice
        Parcel ID: 12-345-678
        Owner Name: Jane Smith
        Property Address: 456 Oak Avenue
        Market Value: $250,000
        Tax Year: 2023
        """

    def tearDown(self):
        """Clean up after tests."""
        self.parser.clean()

    @patch('pdfplumber.open')
    def test_parse_valid_pdf(self, mock_pdf_open):
        """Test parsing valid PDF content."""
        # Mock PDF extraction
        mock_page = Mock()
        mock_page.extract_text.return_value = self.pdf_content
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf_open.return_value = mock_pdf

        result = self.parser.parse("dummy.pdf")

        self.assertEqual(result['parcel_id'], '12-345-678')
        self.assertEqual(result['owner_name'], 'Jane Smith')
        self.assertEqual(result['property_address'], '456 Oak Avenue')
        self.assertEqual(result['market_value'], 250000.0)
        self.assertEqual(result['tax_year'], 2023)

    def test_validate_valid_data(self):
        """Test validation with valid data."""
        valid_data = {
            'parcel_id': '12-345-678',
            'owner_name': 'Jane Smith',
            'property_address': '456 Oak Avenue',
            'market_value': 250000.0,
            'tax_year': 2023
        }
        self.assertTrue(self.parser.validate(valid_data))

    def test_validate_invalid_parcel_id(self):
        """Test validation with invalid parcel ID format."""
        invalid_data = {
            'parcel_id': '123456789',  # Wrong format
            'owner_name': 'Jane Smith',
            'property_address': '456 Oak Avenue',
            'market_value': 250000.0,
            'tax_year': 2023
        }
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def test_save_data(self):
        """Test saving data to database."""
        mock_cursor = Mock()
        self.mock_db.cursor.return_value = mock_cursor

        test_data = {
            'parcel_id': '12-345-678',
            'owner_name': 'Jane Smith',
            'property_address': '456 Oak Avenue',
            'market_value': 250000.0,
            'tax_year': 2023
        }
        self.parser.save(test_data)

        mock_cursor.execute.assert_called_once()
        self.mock_db.commit.assert_called_once()

class TestClaytonExcelParser(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=DatabaseConnection)
        self.parser = ClaytonExcelParser(connection=self.mock_db)
        
        # Sample Excel data
        self.valid_data = {
            'parcel_id': '12-345-678',
            'owner_name': 'Jane Smith',
            'property_address': '456 Oak Avenue',
            'market_value': 250000.0,
            'tax_year': 2023
        }

    def tearDown(self):
        """Clean up after tests."""
        self.parser.clean()

    def test_parse_excel_data(self):
        """Test parsing Excel data."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            # Create test Excel file
            df = pd.DataFrame([self.valid_data])
            df.to_excel(tmp.name, index=False)
            
            result = self.parser.parse(tmp.name)
            
            self.assertEqual(result['parcel_id'], self.valid_data['parcel_id'])
            self.assertEqual(result['owner_name'], self.valid_data['owner_name'])
            self.assertEqual(result['market_value'], self.valid_data['market_value'])
            
            os.unlink(tmp.name)

    def test_parse_empty_excel(self):
        """Test parsing empty Excel file."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            # Create empty Excel file
            df = pd.DataFrame()
            df.to_excel(tmp.name, index=False)
            
            with self.assertRaises(DataFormatError):
                self.parser.parse(tmp.name)
            
            os.unlink(tmp.name)

    def test_validate_invalid_market_value(self):
        """Test validation with invalid market value."""
        invalid_data = self.valid_data.copy()
        invalid_data['market_value'] = -1000
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def test_validate_invalid_tax_year(self):
        """Test validation with invalid tax year."""
        invalid_data = self.valid_data.copy()
        invalid_data['tax_year'] = 1800  # Too old
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

if __name__ == '__main__':
    unittest.main()
