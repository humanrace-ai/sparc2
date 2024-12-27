from typing import Any, Dict, List, Optional
import pandas as pd
import geopandas as gpd
from pathlib import Path

from .base import BaseParser
from .exceptions import ValidationError, DataFormatError
from .utils.validation import (
    validate_type,
    validate_string_format,
    validate_required_fields,
    validate_numeric_range
)

class CivicsourceParser(BaseParser):
    """Parser for Civicsource data including property cards and GIS information."""

    REQUIRED_FIELDS = [
        "property_id",
        "address",
        "owner_name",
        "assessed_value",
        "tax_status",
        "coordinates"
    ]

    def __init__(self, connection=None):
        super().__init__(connection)
        self.data_frame = None
        self.gis_data = None

    def parse(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse input data from various sources."""
        try:
            if isinstance(data.get('excel_path'), (str, Path)):
                self.data_frame = pd.read_excel(data['excel_path'])
            elif isinstance(data.get('csv_path'), (str, Path)):
                self.data_frame = pd.read_csv(data['csv_path'])
            elif isinstance(data.get('gis_path'), (str, Path)):
                self.gis_data = gpd.read_file(data['gis_path'])
            else:
                raise DataFormatError("No valid input data source provided")

            parsed_data = self._transform_data()
            return parsed_data

        except Exception as e:
            self.log(40, f"Error parsing data: {str(e)}")
            raise DataFormatError(f"Failed to parse input data: {str(e)}")

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate parsed data against required schema."""
        try:
            # Check required fields
            if not validate_required_fields(data, self.REQUIRED_FIELDS):
                raise ValidationError("Missing required fields")

            # Validate property ID format (assumed format: ABC-12345)
            if not validate_string_format(data['property_id'], r'^[A-Z]{3}-\d{5}$'):
                raise ValidationError("Invalid property ID format")

            # Validate assessed value
            if not validate_numeric_range(
                float(data['assessed_value']), 
                min_val=0, 
                max_val=1e9
            ):
                raise ValidationError("Invalid assessed value")

            # Validate coordinates
            coords = data['coordinates']
            if not (
                isinstance(coords, dict) and
                validate_numeric_range(coords.get('lat', 0), -90, 90) and
                validate_numeric_range(coords.get('lon', 0), -180, 180)
            ):
                raise ValidationError("Invalid coordinates")

            return True

        except Exception as e:
            self.log(40, f"Validation error: {str(e)}")
            raise ValidationError(str(e))

    def save(self, data: Dict[str, Any]) -> None:
        """Save parsed and validated data to database."""
        with self.transaction():
            try:
                # Implementation would depend on specific database schema
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO properties (
                        property_id, address, owner_name, 
                        assessed_value, tax_status, latitude, longitude
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['property_id'],
                    data['address'],
                    data['owner_name'],
                    data['assessed_value'],
                    data['tax_status'],
                    data['coordinates']['lat'],
                    data['coordinates']['lon']
                ))
            except Exception as e:
                self.log(40, f"Error saving to database: {str(e)}")
                raise

    def clean(self) -> None:
        """Clean up resources."""
        if self.data_frame is not None:
            del self.data_frame
        if self.gis_data is not None:
            del self.gis_data

    def _transform_data(self) -> Dict[str, Any]:
        """Transform parsed data into standardized format."""
        if self.data_frame is not None:
            # Transform DataFrame data
            return self._transform_tabular_data()
        elif self.gis_data is not None:
            # Transform GIS data
            return self._transform_gis_data()
        else:
            raise DataFormatError("No data available for transformation")

    def _transform_tabular_data(self) -> Dict[str, Any]:
        """Transform Excel/CSV data into standardized format."""
        row = self.data_frame.iloc[0]
        return {
            'property_id': str(row.get('property_id', '')),
            'address': str(row.get('address', '')),
            'owner_name': str(row.get('owner_name', '')),
            'assessed_value': float(row.get('assessed_value', 0)),
            'tax_status': str(row.get('tax_status', '')),
            'coordinates': {
                'lat': float(row.get('latitude', 0)),
                'lon': float(row.get('longitude', 0))
            }
        }

    def _transform_gis_data(self) -> Dict[str, Any]:
        """Transform GIS data into standardized format."""
        feature = self.gis_data.iloc[0]
        return {
            'property_id': str(feature.get('property_id', '')),
            'address': str(feature.get('address', '')),
            'owner_name': str(feature.get('owner_name', '')),
            'assessed_value': float(feature.get('assessed_value', 0)),
            'tax_status': str(feature.get('tax_status', '')),
            'coordinates': {
                'lat': float(feature.geometry.centroid.y),
                'lon': float(feature.geometry.centroid.x)
            }
        }
