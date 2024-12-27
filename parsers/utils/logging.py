import logging
import sys
from typing import Optional

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(console_handler)
        
        # File handler
        file_handler = logging.FileHandler(f"{name}.log")
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        
    logger.setLevel(level)
    return logger

def set_log_level(logger: logging.Logger, level: int) -> None:
    """Set the log level for a logger instance."""
    logger.setLevel(level)

def add_file_handler(logger: logging.Logger, filename: str, 
                    level: Optional[int] = None) -> None:
    """Add a file handler to the logger."""
    handler = logging.FileHandler(filename)
    if level:
        handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(handler)

def add_parser_fields(logger: logging.Logger, parser_name: str, county: str) -> None:
    """Add parser-specific context fields to logger.
    
    Args:
        logger: Logger instance to enhance
        parser_name: Name of the parser
        county: County being parsed
    """
    class ParserFilter(logging.Filter):
        def filter(self, record):
            record.parser_name = parser_name
            record.county = county
            return True
            
    logger.addFilter(ParserFilter())
    # Update format to include new fields
    for handler in logger.handlers:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - [%(parser_name)s:%(county)s] - %(levelname)s - %(message)s'
        ))

class ParsingStats:
    """Track parsing statistics."""
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.records_processed = 0
        self.records_failed = 0
        self.start_time = None
        
    def log_parsing_stats(self) -> None:
        """Log current parsing statistics."""
        success_rate = ((self.records_processed - self.records_failed) / 
                       max(self.records_processed, 1) * 100)
        
        self.logger.info(
            "Parsing Statistics: "
            f"Processed={self.records_processed}, "
            f"Failed={self.records_failed}, "
            f"Success Rate={success_rate:.1f}%"
        )
