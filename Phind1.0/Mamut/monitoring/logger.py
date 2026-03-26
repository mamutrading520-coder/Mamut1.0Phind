"""Centralized logger setup for Mamut"""
import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up and return a logger with the given name.

    Args:
        name: Logger name (shown in log output)
        level: Optional log level override (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    log_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
    logger.setLevel(log_level)

    return logger
