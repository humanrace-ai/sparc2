import unittest
from unittest.mock import Mock, patch
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pathlib import Path
import tempfile
import os

from parsers.civicsource import CivicsourceParser
from parsers.exceptions import ValidationError, DataFormatError
from parsers.utils.db import DatabaseConnection

class TestCivicsourceParser(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=DatabaseConnection)
        self.parser = CivicsourceParser(connection=self.mock_db)
        
        # Create sample data
        self.valid_data = {
            'property_id': 'ABC-12345',
            'address': '123 Main St',
            'owner_name': 'John Doe',
            'assessed_value': 150000.0,
            'tax_status': 'current',
            'coordinates': {'lat': 40.7128, 'lon': -74.0060}
        }

    def tearDown(self):
        """Clean up after tests."""
        self.parser.clean()

    def test_validate_valid_data(self):
        """Test validation with valid data."""
        self.assertTrue(self.parser.validate(self.valid_data))

    def test_validate_invalid_property_id(self):
        """Test validation with invalid property ID format."""
        invalid_data = self.valid_data.copy()
        invalid_data['property_id'] = '123'
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def test_validate_invalid_assessed_value(self):
        """Test validation with invalid assessed value."""
        invalid_data = self.valid_data.copy()
        invalid_data['assessed_value'] = -1000
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def test_validate_invalid_coordinates(self):
        """Test validation with invalid coordinates."""
        invalid_data = self.valid_data.copy()
        invalid_data['coordinates'] = {'lat': 91, 'lon': -74.0060}
        
        with self.assertRaises(ValidationError):
            self.parser.validate(invalid_data)

    def test_parse_excel_data(self):
        """Test parsing Excel data."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            # Create test Excel file
            df = pd.DataFrame([self.valid_data])
            df.to_excel(tmp.name, index=False)
            
            result = self.parser.parse({'excel_path': tmp.name})
            
            self.assertEqual(result['property_id'], self.valid_data['property_id'])
            self.assertEqual(result['address'], self.valid_data['address'])
            
            os.unlink(tmp.name)

    def test_parse_csv_data(self):
        """Test parsing CSV data."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            # Create test CSV file
            df = pd.DataFrame([self.valid_data])
            df.to_csv(tmp.name, index=False)
            
            result = self.parser.parse({'csv_path': tmp.name})
            
            self.assertEqual(result['property_id'], self.valid_data['property_id'])
            self.assertEqual(result['address'], self.valid_data['address'])
            
            os.unlink(tmp.name)

    def test_parse_gis_data(self):
        """Test parsing GIS data."""
        # Create sample GIS data
        geometry = [Point(-74.0060, 40.7128)]
        gis_data = {
            'property_id': ['ABC-12345'],
            'address': ['123 Main St'],
            'owner_name': ['John Doe'],
            'assessed_value': [150000.0],
            'tax_status': ['current'],
            'geometry': geometry
        }
        gdf = gpd.GeoDataFrame(gis_data, geometry='geometry')
        
        with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as tmp:
            gdf.to_file(tmp.name, driver='GeoJSON')
            
            result = self.parser.parse({'gis_path': tmp.name})
            
            self.assertEqual(result['property_id'], self.valid_data['property_id'])
            self.assertEqual(result['coordinates']['lat'], 40.7128)
            self.assertEqual(result['coordinates']['lon'], -74.0060)
            
            os.unlink(tmp.name)

    def test_save_data(self):
        """Test saving data to database."""
        mock_cursor = Mock()
        self.mock_db.cursor.return_value = mock_cursor
        
        self.parser.save(self.valid_data)
        
        # Verify database interaction
        mock_cursor.execute.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_invalid_data_source(self):
        """Test parsing with invalid data source."""
        with self.assertRaises(DataFormatError):
            self.parser.parse({'invalid_path': 'some/path'})

if __name__ == '__main__':
    unittest.main()
