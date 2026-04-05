import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path.home() / ".showmaster"
LOG_FILE = LOG_DIR / "audit.log"

def setup_logging():
    """Setup centralized audit logging with rotation."""
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("showmaster")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if setup_logging() is called multiple times
    if not logger.handlers:
        # Rotating file handler: 5 files max, 1MB each
        handler = RotatingFileHandler(
            LOG_FILE, maxBytes=1024*1024, backupCount=5
        )
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] (%(name)s): %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Also console handler for development
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
    
    return logger

def get_logger(name="showmaster"):
    """Helper to get a sub-logger for a specific component."""
    return logging.getLogger(f"showmaster.{name}")

# Initialize global logger on import
setup_logging()
