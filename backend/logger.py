import logging
import os
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "io_guard.log")

def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # Capture everything typical of a "verbose" mode

    # Check if handlers are already added to avoid duplicates
    if not logger.handlers:
        # 1. File Handler (Persistent logs)
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3)
        file_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - [%(name)s] - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 2. Console Handler (Docker logs)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('[%(levelname)s] [%(name)s] %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger
