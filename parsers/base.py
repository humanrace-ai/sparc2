from abc import ABC, abstractmethod
import logging
from contextlib import contextmanager
from typing import Any, Optional

from .exceptions import DatabaseError
from .utils.db import DatabaseConnection
from .utils.logging import get_logger

class BaseParser(ABC):
    """Abstract base class for all parsers."""
    
    def __init__(self, connection: Optional[DatabaseConnection] = None):
        self.logger = get_logger(self.__class__.__name__)
        self.connection = connection
        
    @abstractmethod
    def parse(self, data: Any) -> Any:
        """Parse the input data."""
        pass
        
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate the parsed data."""
        pass
        
    @abstractmethod
    def save(self, data: Any) -> None:
        """Save the parsed and validated data."""
        pass
        
    @abstractmethod
    def clean(self) -> None:
        """Clean up any resources."""
        pass
        
    def log(self, level: int, message: str) -> None:
        """Log a message at the specified level."""
        self.logger.log(level, message)
        
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        if not self.connection:
            raise DatabaseError("No database connection available")
            
        try:
            yield
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise DatabaseError(f"Transaction failed: {str(e)}")
