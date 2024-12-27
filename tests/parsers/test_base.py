import unittest
from unittest.mock import MagicMock, patch
from parsers.base import BaseParser
from parsers.exceptions import DatabaseError
from parsers.utils.db import DatabaseConnection

class TestParser(BaseParser):
    """Concrete implementation of BaseParser for testing."""
    def parse(self, data):
        return data
        
    def validate(self, data):
        return True
        
    def save(self, data):
        pass
        
    def clean(self):
        pass

class TestBaseParser(unittest.TestCase):
    def setUp(self):
        self.db_connection = MagicMock(spec=DatabaseConnection)
        self.parser = TestParser(self.db_connection)

    def test_parser_initialization(self):
        self.assertIsNotNone(self.parser.logger)
        self.assertEqual(self.parser.connection, self.db_connection)

    def test_logging(self):
        with patch.object(self.parser.logger, 'log') as mock_log:
            self.parser.log(20, "test message")
            mock_log.assert_called_once_with(20, "test message")

    def test_transaction_context_manager(self):
        with self.parser.transaction():
            self.db_connection.commit.assert_not_called()
        self.db_connection.commit.assert_called_once()

    def test_transaction_rollback_on_error(self):
        with self.assertRaises(DatabaseError):
            with self.parser.transaction():
                raise ValueError("Test error")
        self.db_connection.rollback.assert_called_once()

    def test_no_connection_raises_error(self):
        parser = TestParser(None)
        with self.assertRaises(DatabaseError):
            with parser.transaction():
                pass

if __name__ == '__main__':
    unittest.main()
