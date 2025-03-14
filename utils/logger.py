#!/usr/bin/env python3
"""
Logging configuration module.
"""
import os
import logging
import sys
from datetime import datetime

# Create a custom logger
logger = logging.getLogger("screen-audio-manager")

# Set the default level
logger.setLevel(logging.INFO)

# Create handlers
c_handler = logging.StreamHandler(sys.stdout)
log_dir = os.path.expanduser("~/.local/share/screen-audio-manager/logs")

# Create log directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Create a log file with date in the name
log_file = os.path.join(log_dir, f"manager_{datetime.now().strftime('%Y-%m-%d')}.log")
f_handler = logging.FileHandler(log_file)

# Create formatters and add them to handlers
c_format = logging.Formatter('%(levelname)s: %(message)s')
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

def set_verbose(verbose: bool = True) -> None:
    """
    Set the verbosity level of the logger.
    
    Args:
        verbose: If True, set level to DEBUG, otherwise INFO
    """
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.debug("Debug logging enabled")

def log_exception(e: Exception) -> None:
    """
    Log an exception with traceback.
    
    Args:
        e: Exception to log
    """
    logger.exception(f"An error occurred: {str(e)}")
