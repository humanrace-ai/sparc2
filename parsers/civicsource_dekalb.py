from typing import Any, Dict, Optional
import requests
import jwt
from datetime import datetime, timedelta
from decimal import Decimal
from urllib.parse import urljoin

from .civicsource import CivicsourceParser
from .exceptions import ValidationError, DataFormatError, AuthenticationError
from .utils.validation import (
    validate_type,
    validate_string_format,
    validate_required_fields,
    validate_numeric_range,
    validate_dekalb_id,
    validate_tax_amount,
    validate_date_format
)

class DeKalbCivicsourceParser(CivicsourceParser):
    """Parser for DeKalb County Civicsource data with authentication handling.
    
    Handles DeKalb County specific property data format and validation rules.
    Includes additional fields like property_class and total_due.
    """

    BASE_URL = "https://dekalb.civicsource.com/api/v2/"
    
    REQUIRED_FIELDS = [
        "tax_id",
        "address",
        "owner_name",
        "assessed_value",
        "tax_status",
        "coordinates",
        "property_class",
        "total_due",
        "sale_date"
    ]
    
    def __init__(self, connection=None, credentials: Dict[str, str] = None):
        super().__init__(connection)
        self.credentials = credentials or {}
        self.session = requests.Session()
        self.auth_token = None
        self.token_expiry = None

    def authenticate(self) -> bool:
        """Authenticate with DeKalb Civicsource API."""
        try:
            response = self.session.post(
                urljoin(self.BASE_URL, "auth/login"),
                json={
                    "email": self.credentials.get("email"),
                    "password": self.credentials.get("password")
                }
            )
            response.raise_for_status()
            
            auth_data = response.json()
            self.auth_token = auth_data["token"]
            self.token_expiry = datetime.now() + timedelta(hours=24)
            
            self.session.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
            return True

        except requests.exceptions.RequestException as e:
            self.log(40, f"Authentication failed: {str(e)}")
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")

    def verify_email(self, verification_code: str) -> bool:
        """Verify email address with provided code."""
        try:
            response = self.session.post(
                urljoin(self.BASE_URL, "auth/verify-email"),
                json={"code": verification_code}
            )
            response.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            self.log(40, f"Email verification failed: {str(e)}")
            raise AuthenticationError(f"Failed to verify email: {str(e)}")

    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate parsed data against DeKalb County specific schema.
        
        Args:
            data: Dictionary containing parsed property data
            
        Returns:
            bool: True if data is valid
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Check required fields
            if not validate_required_fields(data, self.REQUIRED_FIELDS):
                raise ValidationError("Missing required fields")

            # Validate DeKalb property ID format
            if not validate_dekalb_id(data['tax_id']):
                raise ValidationError("Invalid DeKalb County tax ID format")

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
                validate_numeric_range(coords.get('lat', 0), 33.5, 34.0) and  # DeKalb County lat range
                validate_numeric_range(coords.get('lon', 0), -84.4, -83.8)    # DeKalb County lon range
            ):
                raise ValidationError("Invalid coordinates for DeKalb County")

            # Validate property class
            if not validate_string_format(data['property_class'], r'^[A-Z]\d{2}$'):
                raise ValidationError("Invalid property class format")

            # Validate total due amount
            if not validate_tax_amount(data['total_due']):
                raise ValidationError("Invalid total due amount")

            # Validate sale date
            if not validate_date_format(data['sale_date']):
                raise ValidationError("Invalid sale date format")

            return True

        except Exception as e:
            self.log(40, f"DeKalb validation error: {str(e)}")
            raise ValidationError(str(e))

    def refresh_session(self) -> bool:
        """Refresh authentication session if token is expired."""
        if not self.auth_token or not self.token_expiry:
            return self.authenticate()
            
        if datetime.now() >= self.token_expiry:
            try:
                response = self.session.post(
                    urljoin(self.BASE_URL, "auth/refresh"),
                    headers={"Authorization": f"Bearer {self.auth_token}"}
                )
                response.raise_for_status()
                
                auth_data = response.json()
                self.auth_token = auth_data["token"]
                self.token_expiry = datetime.now() + timedelta(hours=24)
                
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                return True

            except requests.exceptions.RequestException as e:
                self.log(40, f"Session refresh failed: {str(e)}")
                return self.authenticate()
                
        return True

    def parse(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Override parse method to ensure authentication."""
        if not self.refresh_session():
            raise AuthenticationError("Failed to establish valid session")
        return super().parse(data)

    def clean(self) -> None:
        """Clean up resources including session."""
        super().clean()
        if self.session:
            self.session.close()
