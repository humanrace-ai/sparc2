import unittest
import logging
import os
from parsers.utils.logging import get_logger, set_log_level, add_file_handler

class TestLogging(unittest.TestCase):
    def setUp(self):
        self.logger_name = "test_logger"
        self.test_log_file = "test.log"

    def tearDown(self):
        # Clean up any log files created during tests
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_get_logger(self):
        logger = get_logger(self.logger_name)
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, self.logger_name)
        self.assertEqual(logger.level, logging.INFO)

    def test_set_log_level(self):
        logger = get_logger(self.logger_name)
        set_log_level(logger, logging.DEBUG)
        self.assertEqual(logger.level, logging.DEBUG)

    def test_add_file_handler(self):
        logger = get_logger(self.logger_name)
        initial_handlers = len(logger.handlers)
        add_file_handler(logger, self.test_log_file)
        self.assertEqual(len(logger.handlers), initial_handlers + 1)
        
    def test_logger_output(self):
        logger = get_logger(self.logger_name)
        test_message = "Test log message"
        logger.info(test_message)
        
        # Verify log file exists and contains message
        with open(f"{self.logger_name}.log", 'r') as f:
            log_content = f.read()
            self.assertIn(test_message, log_content)

if __name__ == '__main__':
    unittest.main()
