import unittest
from parsers.exceptions import ValidationError, DataFormatError
from parsers.utils.validation import (
    validate_cobb_id,
    validate_clayton_parcel,
    validate_tax_amount
)

class TestValidation(unittest.TestCase):
    def test_validation_error(self):
        with self.assertRaises(ValidationError):
            raise ValidationError("Test validation error")

    def test_data_format_error(self):
        with self.assertRaises(DataFormatError):
            raise DataFormatError("Test data format error")

    def test_error_inheritance(self):
        self.assertTrue(issubclass(ValidationError, Exception))
        self.assertTrue(issubclass(DataFormatError, Exception))
        
    def test_validate_cobb_id(self):
        # Valid formats
        self.assertTrue(validate_cobb_id('1234567890123'))
        self.assertTrue(validate_cobb_id('12345-67890-123'))
        
        # Invalid formats
        self.assertFalse(validate_cobb_id('123456789012'))  # Too short
        self.assertFalse(validate_cobb_id('12345678901234'))  # Too long
        self.assertFalse(validate_cobb_id('abcd567890123'))  # Contains letters
        
    def test_validate_clayton_parcel(self):
        # Valid format
        self.assertTrue(validate_clayton_parcel('123A12345678'))
        
        # Invalid formats
        self.assertFalse(validate_clayton_parcel('12A12345678'))  # Too few leading digits
        self.assertFalse(validate_clayton_parcel('1234A2345678'))  # Too many leading digits
        self.assertFalse(validate_clayton_parcel('123412345678'))  # Missing letter
        self.assertFalse(validate_clayton_parcel('123A1234567'))   # Too few trailing digits
        
    def test_validate_tax_amount(self):
        # Valid amounts
        self.assertTrue(validate_tax_amount(1000.50))
        self.assertTrue(validate_tax_amount(1.00))
        self.assertTrue(validate_tax_amount(9999999.99))
        
        # Invalid amounts
        self.assertFalse(validate_tax_amount(0))
        self.assertFalse(validate_tax_amount(-100))
        self.assertFalse(validate_tax_amount(10000000.01))  # Exceeds maximum

if __name__ == '__main__':
    unittest.main()
