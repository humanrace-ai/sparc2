from typing import Any, Dict, Optional
from datetime import datetime
import re

from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError

from .base import BaseParser
from .exceptions import ValidationError, DataFormatError

class CobbPDFParser(BaseParser):
    """Parser for Cobb County PDF tax documents."""
    
    REQUIRED_FIELDS = [
        'property_id',
        'location_address',
        'district',
        'land_lot',
        'tax_amount',
        'assessment_date'
    ]
    
    def __init__(self, connection=None):
        super().__init__(connection)
        self.data = {}
    
    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """Extract and parse data from Cobb County PDF."""
        try:
            text = extract_text(pdf_path)
            self.log(20, f"Successfully extracted text from {pdf_path}")
            
            # Extract key fields using regex patterns
            self.data = {
                'property_id': self._extract_property_id(text),
                'location_address': self._extract_address(text),
                'district': self._extract_district(text),
                'land_lot': self._extract_land_lot(text),
                'tax_amount': self._extract_tax_amount(text),
                'assessment_date': self._extract_date(text)
            }
            
            return self.data
            
        except PDFSyntaxError as e:
            raise DataFormatError(f"Invalid PDF format: {str(e)}")
        except Exception as e:
            self.log(40, f"Error parsing PDF: {str(e)}")
            raise
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate extracted data meets Cobb County format requirements."""
        try:
            # Check all required fields are present
            for field in self.REQUIRED_FIELDS:
                if not data.get(field):
                    raise ValidationError(f"Missing required field: {field}")
            
            # Validate property ID format (e.g., XX-XXXX-XX-XXX)
            if not re.match(r'^\d{2}-\d{4}-\d{2}-\d{3}$', data['property_id']):
                raise ValidationError("Invalid property ID format")
                
            # Validate tax amount is numeric and positive
            if not isinstance(data['tax_amount'], (int, float)) or data['tax_amount'] < 0:
                raise ValidationError("Invalid tax amount")
                
            # Validate date format
            try:
                datetime.strptime(data['assessment_date'], '%Y-%m-%d')
            except ValueError:
                raise ValidationError("Invalid date format")
                
            self.log(20, "Data validation successful")
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            self.log(40, f"Validation error: {str(e)}")
            raise ValidationError(str(e))
    
    def save(self, data: Dict[str, Any]) -> None:
        """Save parsed data to database."""
        with self.transaction():
            query = """
                INSERT INTO cobb_properties 
                (property_id, location_address, district, land_lot, 
                tax_amount, assessment_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """
            params = (
                data['property_id'],
                data['location_address'],
                data['district'],
                data['land_lot'],
                data['tax_amount'],
                data['assessment_date']
            )
            
            try:
                self.connection.execute(query, params)
                self.log(20, f"Saved property {data['property_id']} to database")
            except Exception as e:
                self.log(40, f"Database error: {str(e)}")
                raise
    
    def clean(self) -> None:
        """Clean up any resources."""
        self.data = {}
    
    def _extract_property_id(self, text: str) -> str:
        match = re.search(r'Property ID:\s*(\d{2}-\d{4}-\d{2}-\d{3})', text)
        if not match:
            raise DataFormatError("Could not find property ID")
        return match.group(1)
    
    def _extract_address(self, text: str) -> str:
        match = re.search(r'Location Address:\s*(.+?)(?=\n|$)', text)
        if not match:
            raise DataFormatError("Could not find location address")
        return match.group(1).strip()
    
    def _extract_district(self, text: str) -> str:
        match = re.search(r'District:\s*(\d+)', text)
        if not match:
            raise DataFormatError("Could not find district")
        return match.group(1)
    
    def _extract_land_lot(self, text: str) -> str:
        match = re.search(r'Land Lot:\s*(\d+)', text)
        if not match:
            raise DataFormatError("Could not find land lot")
        return match.group(1)
    
    def _extract_tax_amount(self, text: str) -> float:
        match = re.search(r'Tax Amount:\s*\$?([\d,]+\.?\d*)', text)
        if not match:
            raise DataFormatError("Could not find tax amount")
        return float(match.group(1).replace(',', ''))
    
    def _extract_date(self, text: str) -> str:
        match = re.search(r'Assessment Date:\s*(\d{4}-\d{2}-\d{2})', text)
        if not match:
            raise DataFormatError("Could not find assessment date")
        return match.group(1)
