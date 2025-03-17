#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logger utility for ChuzoBot
Enhanced with better formatting and rotation settings
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

from config import LOG_LEVEL

def setup_logger(name, level=LOG_LEVEL, log_file='chuzobot.log'):
    """Set up and return a logger with the specified name and level.
    
    Creates a logger with both console and file handlers,
    with proper formatting and rotation settings.
    
    Args:
        name: Name of the logger, typically __name__
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name of the log file
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Convert string level to logging level
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # Create formatter with more detailed format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Less verbose on console
    console_handler.setFormatter(formatter)
    
    # Create file handler with improved rotation settings
    file_handler = RotatingFileHandler(
        os.path.join('logs', log_file),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10          # Keep more backups
    )
    file_handler.setLevel(logging.DEBUG)    # Full detail in log file
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Log logger creation
    logger.debug(f"Logger {name} initialized at {datetime.now().isoformat()}")
    
    return logger

def get_logger(name):
    """Get an existing logger or create a new one.
    
    Args:
        name: Name of the logger to retrieve or create
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    
    return logger
