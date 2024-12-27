from typing import Any, Optional, List, Dict
from contextlib import contextmanager
import logging
from threading import local

class DatabaseConnection:
    """Database connection wrapper."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.logger = logging.getLogger(__name__)
        
    def connect(self) -> None:
        """Establish database connection."""
        try:
            # Implement actual database connection logic here
            pass
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise
            
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
            except Exception as e:
                self.logger.error(f"Error closing connection: {str(e)}")
                
    def commit(self) -> None:
        """Commit current transaction."""
        if self.connection:
            self.connection.commit()
            
    def rollback(self) -> None:
        """Rollback current transaction."""
        if self.connection:
            self.connection.rollback()
            
# Thread-local storage for nested transaction tracking
_transaction_local = local()

def batch_insert(connection: DatabaseConnection, table: str, records: List[Dict]) -> None:
    """Perform optimized batch insert of records.
    
    Args:
        connection: Database connection instance
        table: Target table name
        records: List of record dictionaries to insert
    """
    if not records:
        return
        
    # Extract column names from first record
    columns = list(records[0].keys())
    
    # Create parameterized query
    placeholders = ','.join(['%s'] * len(columns))
    column_names = ','.join(columns)
    query = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
    
    # Convert records to value tuples
    values = [[record[column] for column in columns] for record in records]
    
    try:
        connection.cursor.executemany(query, values)
    except Exception as e:
        connection.logger.error(f"Batch insert failed: {str(e)}")
        raise

@contextmanager
def transaction_scope(connection: DatabaseConnection):
    """Provide transaction scope context manager with nested transaction support."""
    # Initialize transaction count for this thread
    if not hasattr(_transaction_local, 'count'):
        _transaction_local.count = 0
    
    try:
        _transaction_local.count += 1
        yield
        
        # Only commit on outermost transaction
        _transaction_local.count -= 1
        if _transaction_local.count == 0:
            connection.commit()
    except Exception:
        _transaction_local.count -= 1
        if _transaction_local.count == 0:
            connection.rollback()
        raise
