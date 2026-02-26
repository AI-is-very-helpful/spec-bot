"""Logging configuration for Spec Bot"""

import logging
import sys
from typing import Optional


class SpecBotLogger:
    """Structured logger for Spec Bot"""
    
    _instance: Optional[logging.Logger] = None
    
    @classmethod
    def get_logger(cls, name: str = "spec_bot") -> logging.Logger:
        """Get or create logger instance"""
        if cls._instance is not None:
            return cls._instance.getChild(name)
        
        logger = logging.getLogger(name)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger.getChild(name)
        
        # Set level
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        cls._instance = logger
        return logger.getChild(name)
    
    @classmethod
    def configure_json_logger(cls, name: str = "spec_bot") -> logging.Logger:
        """Configure JSON logger for production"""
        # Lazy import to avoid dependency issues in dev
        from pythonjsonlogger import jsonlogger
        
        logger = logging.getLogger(name)
        
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(name)s %(levelname)s %(message)s"
            )
        )
        
        logger.addHandler(handler)
        
        if cls._instance is None:
            cls._instance = logger
        
        return logger


def get_logger(name: str = "spec_bot") -> logging.Logger:
    """Convenience function to get logger"""
    return SpecBotLogger.get_logger(name)
