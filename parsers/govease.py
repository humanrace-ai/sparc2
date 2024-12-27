from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import requests
from PIL import Image
from io import BytesIO

from .base import BaseParser
from .exceptions import ValidationError, DataFormatError, DatabaseError

@dataclass
class PropertyData:
    """Data structure for property information."""
    parcel_id: str
    property_address: str
    owner_name: str
    tax_amount_due: float
    assessed_value: float
    sale_datetime: datetime
    opening_bid: float
    latitude: float
    longitude: float
    image_urls: List[str]
    
class GovEaseParser(BaseParser):
    """Parser for GovEase property data format."""
    
    REQUIRED_FIELDS = {
        'parcel_id': str,
        'property_address': str,
        'owner_name': str,
        'tax_amount_due': float,
        'assessed_value': float,
        'sale_datetime': datetime,
        'opening_bid': float,
        'latitude': float,
        'longitude': float,
        'image_urls': list
    }
    
    def __init__(self, connection=None):
        super().__init__(connection)
        self.data_frame = None
        
    def parse(self, data: Union[str, pd.DataFrame]) -> List[PropertyData]:
        """Parse input data from CSV/Excel or DataFrame."""
        try:
            if isinstance(data, str):
                if data.endswith('.csv'):
                    self.data_frame = pd.read_csv(data)
                elif data.endswith(('.xls', '.xlsx')):
                    self.data_frame = pd.read_excel(data)
                else:
                    raise DataFormatError(f"Unsupported file format: {data}")
            elif isinstance(data, pd.DataFrame):
                self.data_frame = data
            else:
                raise DataFormatError("Input must be a file path or DataFrame")
                
            # Convert date columns
            self.data_frame['sale_datetime'] = pd.to_datetime(self.data_frame['sale_datetime'])
            
            # Convert to list of PropertyData objects
            properties = []
            for _, row in self.data_frame.iterrows():
                property_data = PropertyData(
                    parcel_id=str(row['parcel_id']),
                    property_address=str(row['property_address']),
                    owner_name=str(row['owner_name']),
                    tax_amount_due=float(row['tax_amount_due']),
                    assessed_value=float(row['assessed_value']),
                    sale_datetime=row['sale_datetime'].to_pydatetime(),
                    opening_bid=float(row['opening_bid']),
                    latitude=float(row['latitude']),
                    longitude=float(row['longitude']),
                    image_urls=self._parse_image_urls(row['image_urls'])
                )
                properties.append(property_data)
                
            return properties
            
        except Exception as e:
            raise DataFormatError(f"Failed to parse data: {str(e)}")
            
    def validate(self, data: List[PropertyData]) -> bool:
        """Validate the parsed property data."""
        for property_data in data:
            # Check all required fields are present
            for field, field_type in self.REQUIRED_FIELDS.items():
                value = getattr(property_data, field)
                if value is None:
                    raise ValidationError(f"Missing required field: {field}")
                if not isinstance(value, field_type):
                    raise ValidationError(f"Invalid type for {field}: expected {field_type}, got {type(value)}")
                    
            # Validate specific field constraints
            if not self._is_valid_parcel_id(property_data.parcel_id):
                raise ValidationError(f"Invalid parcel ID format: {property_data.parcel_id}")
                
            if property_data.tax_amount_due < 0:
                raise ValidationError(f"Tax amount cannot be negative: {property_data.tax_amount_due}")
                
            if property_data.assessed_value <= 0:
                raise ValidationError(f"Assessed value must be positive: {property_data.assessed_value}")
                
            if property_data.opening_bid <= 0:
                raise ValidationError(f"Opening bid must be positive: {property_data.opening_bid}")
                
            if not (-90 <= property_data.latitude <= 90):
                raise ValidationError(f"Invalid latitude: {property_data.latitude}")
                
            if not (-180 <= property_data.longitude <= 180):
                raise ValidationError(f"Invalid longitude: {property_data.longitude}")
                
            # Validate image URLs
            for url in property_data.image_urls:
                if not self._is_valid_image_url(url):
                    raise ValidationError(f"Invalid image URL: {url}")
                    
        return True
        
    def save(self, data: List[PropertyData]) -> None:
        """Save the parsed and validated property data to database."""
        with self.transaction():
            for property_data in data:
                self._save_property(property_data)
                
    def clean(self) -> None:
        """Clean up resources."""
        if self.data_frame is not None:
            del self.data_frame
            self.data_frame = None
            
    def _save_property(self, property_data: PropertyData) -> None:
        """Save a single property record to database."""
        query = """
            INSERT INTO properties (
                parcel_id, property_address, owner_name, tax_amount_due,
                assessed_value, sale_datetime, opening_bid, latitude, longitude
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        values = (
            property_data.parcel_id,
            property_data.property_address,
            property_data.owner_name,
            property_data.tax_amount_due,
            property_data.assessed_value,
            property_data.sale_datetime,
            property_data.opening_bid,
            property_data.latitude,
            property_data.longitude
        )
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, values)
            
            # Save image URLs in related table
            self._save_image_urls(cursor.lastrowid, property_data.image_urls)
            
        except Exception as e:
            raise DatabaseError(f"Failed to save property data: {str(e)}")
            
    def _save_image_urls(self, property_id: int, image_urls: List[str]) -> None:
        """Save image URLs for a property."""
        query = "INSERT INTO property_images (property_id, image_url) VALUES (%s, %s)"
        
        try:
            cursor = self.connection.cursor()
            for url in image_urls:
                cursor.execute(query, (property_id, url))
        except Exception as e:
            raise DatabaseError(f"Failed to save image URLs: {str(e)}")
            
    def _parse_image_urls(self, urls: str) -> List[str]:
        """Parse image URLs from string or list format."""
        if isinstance(urls, str):
            return [url.strip() for url in urls.split(',') if url.strip()]
        elif isinstance(urls, list):
            return [str(url) for url in urls if url]
        else:
            return []
            
    def _is_valid_parcel_id(self, parcel_id: str) -> bool:
        """Validate parcel ID format."""
        # Implement specific parcel ID validation rules
        return bool(parcel_id and len(parcel_id) >= 5)
        
    def _is_valid_image_url(self, url: str) -> bool:
        """Validate image URL and check if it's accessible."""
        try:
            response = requests.head(url, timeout=5)
            content_type = response.headers.get('content-type', '')
            return response.status_code == 200 and 'image' in content_type.lower()
        except:
            return False
