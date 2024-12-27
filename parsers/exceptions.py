class ParserError(Exception):
    """Base exception for all parser errors."""
    pass

class ValidationError(ParserError):
    """Raised when data validation fails."""
    pass

class DatabaseError(ParserError):
    """Raised when database operations fail."""
    pass

class ConfigurationError(ParserError):
    """Raised when parser configuration is invalid."""
    pass

class DataFormatError(ParserError):
    """Raised when data format is incorrect."""
    pass
