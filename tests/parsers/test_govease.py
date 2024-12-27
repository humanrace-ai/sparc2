import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
import pandas as pd
from io import StringIO
from pathlib import Path

from parsers.govease import GovEaseParser, PropertyData
from parsers.exceptions import ValidationError, DataFormatError, DatabaseError
from parsers.utils.db import DatabaseConnection

class TestGovEaseParser(unittest.TestCase):
    def setUp(self):
        self.db_connection = MagicMock(spec=DatabaseConnection)
        self.parser = GovEaseParser(self.db_connection)
        
        # Sample valid property data
        self.valid_data = {
            'parcel_id': ['12345'],
            'property_address': ['123 Main St'],
            'owner_name': ['John Doe'],
            'tax_amount_due': [1000.0],
            'assessed_value': [150000.0],
            'sale_datetime': ['2024-01-15 10:00:00'],
            'opening_bid': [50000.0],
            'latitude': [35.1234],
            'longitude': [-80.5678],
            'image_urls': ['http://example.com/img1.jpg,http://example.com/img2.jpg']
        }
        self.df = pd.DataFrame(self.valid_data)

    def test_parser_initialization(self):
        """Test parser initialization."""
        self.assertIsNotNone(self.parser.logger)
        self.assertEqual(self.parser.connection, self.db_connection)
        self.assertIsNone(self.parser.data_frame)

    @patch('pandas.read_csv')
    def test_parse_csv(self, mock_read_csv):
        """Test parsing CSV data."""
        mock_read_csv.return_value = self.df
        
        result = self.parser.parse('test.csv')
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], PropertyData)
        self.assertEqual(result[0].parcel_id, '12345')
        
        mock_read_csv.assert_called_once()

    @patch('pandas.read_excel')
    def test_parse_excel(self, mock_read_excel):
        """Test parsing Excel data."""
        mock_read_excel.return_value = self.df
        
        result = self.parser.parse('test.xlsx')
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], PropertyData)
        
        mock_read_excel.assert_called_once()

    def test_parse_dataframe(self):
        """Test parsing pandas DataFrame directly."""
        result = self.parser.parse(self.df)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], PropertyData)

    def test_parse_invalid_format(self):
        """Test parsing unsupported file format."""
        with self.assertRaises(DataFormatError):
            self.parser.parse('test.txt')

    def test_validate_valid_data(self):
        """Test validation of valid property data."""
        property_data = PropertyData(
            parcel_id='12345',
            property_address='123 Main St',
            owner_name='John Doe',
            tax_amount_due=1000.0,
            assessed_value=150000.0,
            sale_datetime=datetime(2024, 1, 15, 10, 0),
            opening_bid=50000.0,
            latitude=35.1234,
            longitude=-80.5678,
            image_urls=['http://example.com/img1.jpg']
        )
        self.assertTrue(self.parser.validate([property_data]))

    def test_validate_invalid_parcel_id(self):
        """Test validation with invalid parcel ID."""
        property_data = PropertyData(
            parcel_id='123',  # Too short
            property_address='123 Main St',
            owner_name='John Doe',
            tax_amount_due=1000.0,
            assessed_value=150000.0,
            sale_datetime=datetime(2024, 1, 15, 10, 0),
            opening_bid=50000.0,
            latitude=35.1234,
            longitude=-80.5678,
            image_urls=['http://example.com/img1.jpg']
        )
        with self.assertRaises(ValidationError):
            self.parser.validate([property_data])

    def test_validate_invalid_amounts(self):
        """Test validation with invalid monetary amounts."""
        property_data = PropertyData(
            parcel_id='12345',
            property_address='123 Main St',
            owner_name='John Doe',
            tax_amount_due=-1000.0,  # Negative amount
            assessed_value=150000.0,
            sale_datetime=datetime(2024, 1, 15, 10, 0),
            opening_bid=50000.0,
            latitude=35.1234,
            longitude=-80.5678,
            image_urls=['http://example.com/img1.jpg']
        )
        with self.assertRaises(ValidationError):
            self.parser.validate([property_data])

    def test_validate_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        property_data = PropertyData(
            parcel_id='12345',
            property_address='123 Main St',
            owner_name='John Doe',
            tax_amount_due=1000.0,
            assessed_value=150000.0,
            sale_datetime=datetime(2024, 1, 15, 10, 0),
            opening_bid=50000.0,
            latitude=91.0,  # Invalid latitude
            longitude=-80.5678,
            image_urls=['http://example.com/img1.jpg']
        )
        with self.assertRaises(ValidationError):
            self.parser.validate([property_data])

    @patch('requests.head')
    def test_validate_image_urls(self, mock_head):
        """Test validation of image URLs."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'image/jpeg'}
        mock_head.return_value = mock_response

        property_data = self.parser.parse(self.df)[0]
        self.assertTrue(self.parser.validate([property_data]))
        
        mock_head.assert_called()

    def test_save_property_data(self):
        """Test saving property data to database."""
        mock_cursor = MagicMock()
        self.db_connection.cursor.return_value = mock_cursor
        mock_cursor.lastrowid = 1

        property_data = self.parser.parse(self.df)[0]
        
        with self.parser.transaction():
            self.parser._save_property(property_data)
        
        # Verify database calls
        self.assertEqual(mock_cursor.execute.call_count, 3)  # Main insert + 2 image URLs
        self.db_connection.commit.assert_called_once()

    def test_save_error_handling(self):
        """Test database error handling during save."""
        self.db_connection.cursor.side_effect = Exception("Database error")
        
        property_data = self.parser.parse(self.df)[0]
        
        with self.assertRaises(DatabaseError):
            with self.parser.transaction():
                self.parser._save_property(property_data)
        
        self.db_connection.rollback.assert_called_once()

    def test_clean(self):
        """Test cleanup of parser resources."""
        self.parser.data_frame = self.df
        self.parser.clean()
        self.assertIsNone(self.parser.data_frame)

if __name__ == '__main__':
    unittest.main()
