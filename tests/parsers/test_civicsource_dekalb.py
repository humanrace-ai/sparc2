import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
import json
import pandas as pd
import geopandas as gpd
from pathlib import Path
from datetime import datetime, timedelta

from parsers.civicsource_dekalb import DeKalbCivicsourceParser
from parsers.exceptions import AuthenticationError, ValidationError, DataFormatError

class TestDeKalbCivicsourceParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.fixtures_path = Path(__file__).parent.parent / 'fixtures' / 'dekalb'
        
        # Load auth response fixture
        with open(cls.fixtures_path / 'auth_response.json') as f:
            cls.auth_response = json.load(f)
            
        # Load test data files
        cls.excel_path = cls.fixtures_path / 'excel' / 'sample_export.xlsx'
        cls.csv_path = cls.fixtures_path / 'csv' / 'property_list.csv'
        cls.gis_path = cls.fixtures_path / 'gis' / 'parcels.geojson'
    def setUp(self):
        """Set up test fixtures."""
        self.credentials = {
            "email": "test@example.com",
            "password": "test_password"
        }
        self.mock_db = Mock()
        self.parser = DeKalbCivicsourceParser(
            connection=self.mock_db,
            credentials=self.credentials
        )
        
        # Setup session mock
        self.session_mock = MagicMock()
        self.parser.session = self.session_mock

        # Sample valid DeKalb data
        self.valid_data = {
            'tax_id': '15-123-04-005',
            'address': '123 Dekalb Ave',
            'owner_name': 'John Doe',
            'assessed_value': 250000.0,
            'property_class': 'R3',
            'total_due': 3500.50,
            'sale_date': '2023-06-15',
            'coordinates': {'lat': 33.7490, 'lon': -84.3880}
        }
        
        # Mock authentication
        self.auth_patcher = patch('requests.Session.post')
        self.mock_auth = self.auth_patcher.start()
        self.mock_auth.return_value.ok = True
        self.mock_auth.return_value.json.return_value = self.auth_response

    def test_validate_valid_dekalb_property_id(self):
        """Test validation with valid DeKalb property ID format."""
        self.assertTrue(self.parser.validate(self.valid_data))

    def test_validate_invalid_dekalb_property_id(self):
        """Test validation with invalid DeKalb property ID format."""
        invalid_data = self.valid_data.copy()
        invalid_data['property_id'] = '123-45-678'  # Wrong format
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def test_validate_valid_dekalb_coordinates(self):
        """Test validation with coordinates within DeKalb County bounds."""
        self.assertTrue(self.parser.validate(self.valid_data))

    def test_validate_invalid_dekalb_coordinates(self):
        """Test validation with coordinates outside DeKalb County bounds."""
        invalid_data = self.valid_data.copy()
        invalid_data['coordinates'] = {'lat': 32.0809, 'lon': -81.0912}  # Savannah coordinates
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def test_validate_valid_property_class(self):
        """Test validation with valid property class format."""
        self.assertTrue(self.parser.validate(self.valid_data))

    def test_validate_invalid_property_class(self):
        """Test validation with invalid property class format."""
        invalid_data = self.valid_data.copy()
        invalid_data['property_class'] = 'X123'  # Invalid format
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def test_validate_valid_total_due(self):
        """Test validation with valid total due amount."""
        self.assertTrue(self.parser.validate(self.valid_data))

    def test_validate_invalid_total_due(self):
        """Test validation with invalid total due amount."""
        invalid_data = self.valid_data.copy()
        invalid_data['total_due'] = -500.00  # Negative amount
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def test_validate_valid_sale_date(self):
        """Test validation with valid sale date format."""
        self.assertTrue(self.parser.validate(self.valid_data))

    def test_validate_invalid_sale_date(self):
        """Test validation with invalid sale date format."""
        invalid_data = self.valid_data.copy()
        invalid_data['sale_date'] = '06/15/2023'  # Wrong format
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def tearDown(self):
        """Clean up after tests."""
        self.parser.clean()
        self.auth_patcher.stop()

    @patch('requests.Session.post')
    def test_successful_authentication(self, mock_post):
        """Test successful authentication flow."""
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = self.mock_auth_response
        
        result = self.parser.authenticate()
        
        self.assertTrue(result)
        self.assertEqual(self.parser.auth_token, "mock_jwt_token")
        self.assertIsNotNone(self.parser.token_expiry)
        
        # Verify correct headers were set
        self.assertEqual(
            self.parser.session.headers["Authorization"],
            "Bearer mock_jwt_token"
        )

    @patch('requests.Session.post')
    def test_failed_authentication(self, mock_post):
        """Test authentication failure handling."""
        mock_post.side_effect = requests.exceptions.RequestException("Auth failed")
        
        with self.assertRaises(AuthenticationError):
            self.parser.authenticate()

    @patch('requests.Session.post')
    def test_successful_email_verification(self, mock_post):
        """Test successful email verification."""
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"status": "verified"}
        
        result = self.parser.verify_email("123456")
        
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_failed_email_verification(self, mock_post):
        """Test email verification failure handling."""
        mock_post.side_effect = requests.exceptions.RequestException("Verification failed")
        
        with self.assertRaises(AuthenticationError):
            self.parser.verify_email("123456")

    def test_session_refresh_needed(self):
        """Test session refresh when token is expired."""
        self.parser.auth_token = "expired_token"
        self.parser.token_expiry = datetime.now() - timedelta(hours=1)
        
        with patch.object(self.parser, 'authenticate') as mock_auth:
            mock_auth.return_value = True
            result = self.parser.refresh_session()
            
            self.assertTrue(result)
            mock_auth.assert_called_once()

    def test_session_refresh_not_needed(self):
        """Test session refresh when token is still valid."""
        self.parser.auth_token = "valid_token"
        self.parser.token_expiry = datetime.now() + timedelta(hours=1)
        
        result = self.parser.refresh_session()
        
        self.assertTrue(result)
        self.assertEqual(self.parser.auth_token, "valid_token")

    @patch('requests.Session.post')
    def test_parse_excel_data(self):
        """Test parsing Excel format data."""
        with patch.object(self.parser, 'authenticate') as mock_auth:
            mock_auth.return_value = True
            
            result = self.parser.parse({'excel_path': str(self.excel_path)})
            
            self.assertEqual(result[0]['tax_id'], '15-123-04-005')
            self.assertEqual(result[0]['property_class'], 'R3')
            self.assertEqual(result[0]['total_due'], 3500.50)
            
    def test_parse_csv_data(self):
        """Test parsing CSV format data."""
        with patch.object(self.parser, 'authenticate') as mock_auth:
            mock_auth.return_value = True
            
            result = self.parser.parse({'csv_path': str(self.csv_path)})
            
            self.assertEqual(len(result), 3)
            self.assertEqual(result[1]['tax_id'], '15-124-05-006')
            self.assertEqual(result[1]['property_class'], 'C1')
            
    def test_parse_gis_data(self):
        """Test parsing GIS format data."""
        with patch.object(self.parser, 'authenticate') as mock_auth:
            mock_auth.return_value = True
            
            result = self.parser.parse({'gis_path': str(self.gis_path)})
            
            self.assertEqual(result[0]['coordinates']['lat'], 33.7490)
            self.assertEqual(result[0]['coordinates']['lon'], -84.3880)
            
    def test_parse_with_authentication(self):
        """Test parse method with authentication check."""
        with patch.object(self.parser, 'authenticate') as mock_auth:
            mock_auth.return_value = True
            
            result = self.parser.parse({'excel_path': str(self.excel_path)})
            
            mock_auth.assert_called_once()
            self.assertTrue(isinstance(result, list))
            self.assertTrue(all(isinstance(item, dict) for item in result))

    def test_clean_closes_session(self):
        """Test clean method properly closes session."""
        self.parser.clean()
        self.session_mock.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
