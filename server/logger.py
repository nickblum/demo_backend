import logging
from logging.handlers import RotatingFileHandler
import os
from server.configuration import Settings

def setup_logger():
    settings = Settings()
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)

    # Create logger
    logger = logging.getLogger("thistle_server")
    logger.setLevel(logging.getLevelName(settings.LOG_LEVEL))

    # Create rotating file handler
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_SIZE,
        backupCount=settings.LOG_BACKUP_COUNT
    )

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    return logger

def get_logger(name):
    return logging.getLogger(f"thistle_server.{name}")