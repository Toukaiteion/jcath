"""Logging configuration for jcatch package."""

import logging
import os
from typing import Optional


# Get log level from environment variable
_LOG_LEVEL = os.getenv("JCATCH_LOG_LEVEL", "INFO").upper()

# Get log format from environment variable
_LOG_FORMAT = os.getenv(
    "JCATCH_LOG_FORMAT",
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def _get_level() -> int:
    """Get log level from string."""
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(_LOG_LEVEL, logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with configured level and format.

    Args:
        name: Logger name (e.g., "jcatch.core.processor")

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(_get_level())

    # Only add handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(handler)

    return logger


def configure_logging(level: Optional[int] = None) -> None:
    """Configure root logging for CLI usage.

    Args:
        level: Optional log level (defaults to INFO)
    """
    if level is None:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        force=True,  # Force reconfiguration
    )
