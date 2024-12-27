import unittest
from unittest.mock import MagicMock, patch
from parsers.utils.db import DatabaseConnection, transaction_scope

class TestDatabaseConnection(unittest.TestCase):
    def setUp(self):
        self.connection = DatabaseConnection("test_connection_string")

    def test_initialization(self):
        self.assertEqual(self.connection.connection_string, "test_connection_string")
        self.assertIsNone(self.connection.connection)
        self.assertIsNotNone(self.connection.logger)

    @patch('parsers.utils.db.DatabaseConnection.connect')
    def test_connect(self, mock_connect):
        self.connection.connect()
        mock_connect.assert_called_once()

    def test_disconnect(self):
        self.connection.connection = MagicMock()
        self.connection.disconnect()
        self.connection.connection.close.assert_called_once()

    def test_transaction_scope(self):
        connection = MagicMock()
        with transaction_scope(connection):
            pass
        connection.commit.assert_called_once()

    def test_transaction_scope_rollback(self):
        connection = MagicMock()
        with self.assertRaises(ValueError):
            with transaction_scope(connection):
                raise ValueError("Test error")
        connection.rollback.assert_called_once()

if __name__ == '__main__':
    unittest.main()
