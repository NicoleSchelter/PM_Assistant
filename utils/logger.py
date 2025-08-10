"""
Centralized logging configuration for PM Analysis Tool.

This module provides a consistent logging setup across all components
of the PM Analysis Tool, with support for both console and file output.
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True,
    log_directory: str = "logs",
) -> logging.Logger:
    """
    Set up centralized logging configuration for the PM Analysis Tool.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file name. If None, uses 'pm_analysis.log'
        console_output: Whether to output logs to console
        log_directory: Directory to store log files

    Returns:
        Configured logger instance

    Raises:
        ValueError: If log_level is invalid
    """
    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level.upper() not in valid_levels:
        raise ValueError(f"Invalid log level: {log_level}. Must be one of {valid_levels}")

    # Create log directory if it doesn't exist
    if log_file:
        log_path = Path(log_directory)
        log_path.mkdir(exist_ok=True)
        full_log_path = log_path / log_file
    else:
        log_path = Path(log_directory)
        log_path.mkdir(exist_ok=True)
        full_log_path = log_path / "pm_analysis.log"

    # Define logging configuration
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s - %(message)s"},
            "console": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(full_log_path),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "level": "DEBUG",
                "formatter": "detailed",
                "encoding": "utf-8",
            }
        },
        "loggers": {
            "pm_analysis": {"level": log_level.upper(), "handlers": ["file"], "propagate": False}
        },
    }

    # Add console handler if requested
    if console_output:
        logging_config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level.upper(),
            "formatter": "console",
            "stream": "ext://sys.stdout",
        }
        logging_config["loggers"]["pm_analysis"]["handlers"].append("console")

    # Apply configuration
    logging.config.dictConfig(logging_config)

    # Get and return the logger
    logger = logging.getLogger("pm_analysis")
    logger.info(f"Logging initialized - Level: {log_level}, File: {full_log_path}")

    return logger


def get_logger(name: str = "pm_analysis") -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name, typically the module name

    Returns:
        Logger instance
    """
    return logging.getLogger(f"pm_analysis.{name}")


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.

    Usage:
        class MyClass(LoggerMixin):
            def some_method(self):
                self.logger.info("This is a log message")
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


# Convenience functions for different log levels
def log_debug(message: str, logger_name: str = "pm_analysis") -> None:
    """Log a debug message."""
    logging.getLogger(logger_name).debug(message)


def log_info(message: str, logger_name: str = "pm_analysis") -> None:
    """Log an info message."""
    logging.getLogger(logger_name).info(message)


def log_warning(message: str, logger_name: str = "pm_analysis") -> None:
    """Log a warning message."""
    logging.getLogger(logger_name).warning(message)


def log_error(message: str, logger_name: str = "pm_analysis") -> None:
    """Log an error message."""
    logging.getLogger(logger_name).error(message)


def log_critical(message: str, logger_name: str = "pm_analysis") -> None:
    """Log a critical message."""
    logging.getLogger(logger_name).critical(message)
