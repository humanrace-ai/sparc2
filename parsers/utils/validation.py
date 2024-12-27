from typing import Any, Type, Union, List, Dict
from datetime import datetime
import re
from decimal import Decimal

def validate_type(value: Any, expected_type: Union[Type, tuple]) -> bool:
    """Validate that a value is of the expected type."""
    return isinstance(value, expected_type)

def validate_string_format(value: str, pattern: str) -> bool:
    """Validate string against a regex pattern."""
    return bool(re.match(pattern, value))

def validate_date_format(value: str, format_str: str = "%Y-%m-%d") -> bool:
    """Validate date string format."""
    try:
        datetime.strptime(value, format_str)
        return True
    except ValueError:
        return False

def validate_numeric_range(value: Union[int, float], min_val: float, max_val: float) -> bool:
    """Validate numeric value is within range."""
    return min_val <= value <= max_val

def validate_required_fields(data: Dict, required_fields: List[str]) -> bool:
    """Validate that all required fields are present and non-empty."""
    return all(data.get(field) for field in required_fields)

def validate_cobb_id(value: str) -> bool:
    """Validate Cobb County ID format (13 digits with optional dashes).
    
    Args:
        value: String to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    # Remove any dashes and check if remaining string is 13 digits
    cleaned = value.replace('-', '')
    return bool(re.match(r'^\d{13}$', cleaned))

def validate_clayton_parcel(value: str) -> bool:
    """Validate Clayton County parcel format (12 chars: 3 digits, 1 letter, 8 digits).
    
    Args:
        value: String to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    return bool(re.match(r'^\d{3}[A-Z]\d{8}$', value))

def validate_tax_amount(value: float) -> bool:
    """Validate tax amount (must be positive and under $10M).
    
    Args:
        value: Amount to validate
        
    Returns:
        bool: True if valid amount, False otherwise
    """
    MAX_TAX_AMOUNT = 10_000_000  # $10 million maximum
    return isinstance(value, (float, Decimal)) and 0 < value < MAX_TAX_AMOUNT

def validate_dekalb_id(value: str) -> bool:
    """Validate DeKalb County property ID format (6 digits followed by hyphen and 2 digits).
    
    Args:
        value: String to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    return bool(re.match(r'^\d{6}-\d{2}$', value))
