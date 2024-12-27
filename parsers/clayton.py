from typing import Any, Dict, List, Optional
import pandas as pd
import pdfplumber
from pathlib import Path

from .base import BaseParser
from .exceptions import ValidationError, DataFormatError
from .utils.validation import (
    validate_string_format,
    validate_required_fields,
    validate_numeric_range
)

class ClaytonBaseParser(BaseParser):
    """Base class for Clayton County parsers with shared validation logic."""

    REQUIRED_FIELDS = [
        "parcel_id",
        "owner_name",
        "property_address",
        "market_value",
        "tax_year"
    ]

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate parsed data against Clayton County requirements."""
        try:
            if not validate_required_fields(data, self.REQUIRED_FIELDS):
                raise ValidationError("Missing required fields")

            # Validate parcel ID format (Clayton format: 12-345-678)
            if not validate_string_format(data['parcel_id'], r'^\d{2}-\d{3}-\d{3}$'):
                raise ValidationError("Invalid parcel ID format")

            # Validate market value range
            if not validate_numeric_range(
                float(data['market_value']),
                min_val=0,
                max_val=1e8
            ):
                raise ValidationError("Invalid market value")

            # Validate tax year
            if not validate_numeric_range(
                int(data['tax_year']),
                min_val=1900,
                max_val=2100
            ):
                raise ValidationError("Invalid tax year")

            return True

        except Exception as e:
            self.log(40, f"Validation error: {str(e)}")
            raise ValidationError(str(e))

    def save(self, data: Dict[str, Any]) -> None:
        """Save parsed and validated data to database."""
        with self.transaction():
            try:
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO clayton_properties (
                        parcel_id, owner_name, property_address,
                        market_value, tax_year, last_updated
                    ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    data['parcel_id'],
                    data['owner_name'],
                    data['property_address'],
                    data['market_value'],
                    data['tax_year']
                ))
            except Exception as e:
                self.log(40, f"Error saving to database: {str(e)}")
                raise

class ClaytonPDFParser(ClaytonBaseParser):
    """Parser for Clayton County PDF tax assessment documents."""

    def __init__(self, connection=None):
        super().__init__(connection)
        self.pdf_text = None

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        """Extract and parse data from Clayton County PDF format."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                self.pdf_text = " ".join(page.extract_text() for page in pdf.pages)
            
            return self._extract_fields()

        except Exception as e:
            self.log(40, f"Error parsing PDF: {str(e)}")
            raise DataFormatError(f"Failed to parse PDF: {str(e)}")

    def clean(self) -> None:
        """Clean up resources."""
        if self.pdf_text is not None:
            self.pdf_text = None

    def _extract_fields(self) -> Dict[str, Any]:
        """Extract fields from PDF text using pattern matching."""
        import re
        
        patterns = {
            'parcel_id': r'Parcel ID:?\s*(\d{2}-\d{3}-\d{3})',
            'owner_name': r'Owner Name:?\s*([^\n]+)',
            'property_address': r'Property Address:?\s*([^\n]+)',
            'market_value': r'Market Value:?\s*\$?([\d,]+)',
            'tax_year': r'Tax Year:?\s*(\d{4})'
        }

        extracted = {}
        for field, pattern in patterns.items():
            match = re.search(pattern, self.pdf_text)
            if not match:
                raise DataFormatError(f"Could not find {field} in PDF")
            value = match.group(1).strip()
            if field == 'market_value':
                value = float(value.replace(',', ''))
            elif field == 'tax_year':
                value = int(value)
            extracted[field] = value

        return extracted

class ClaytonExcelParser(ClaytonBaseParser):
    """Parser for Clayton County Excel tax data."""

    def __init__(self, connection=None):
        super().__init__(connection)
        self.data_frame = None

    def parse(self, excel_path: str) -> Dict[str, Any]:
        """Parse Clayton County Excel format."""
        try:
            self.data_frame = pd.read_excel(
                excel_path,
                dtype={
                    'parcel_id': str,
                    'owner_name': str,
                    'property_address': str,
                    'market_value': float,
                    'tax_year': int
                }
            )
            
            if self.data_frame.empty:
                raise DataFormatError("Excel file contains no data")

            return self._transform_row(self.data_frame.iloc[0])

        except Exception as e:
            self.log(40, f"Error parsing Excel: {str(e)}")
            raise DataFormatError(f"Failed to parse Excel: {str(e)}")

    def clean(self) -> None:
        """Clean up resources."""
        if self.data_frame is not None:
            del self.data_frame

    def _transform_row(self, row: pd.Series) -> Dict[str, Any]:
        """Transform Excel row into standardized format."""
        return {
            'parcel_id': str(row['parcel_id']).strip(),
            'owner_name': str(row['owner_name']).strip(),
            'property_address': str(row['property_address']).strip(),
            'market_value': float(row['market_value']),
            'tax_year': int(row['tax_year'])
        }
