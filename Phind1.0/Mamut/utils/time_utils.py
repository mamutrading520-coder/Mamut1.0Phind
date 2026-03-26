"""Time utility functions for Mamut"""
import time
from datetime import datetime, timezone
from typing import Optional


def get_timestamp() -> float:
    """Return current Unix timestamp (seconds since epoch)."""
    return time.time()


def seconds_since(timestamp: float) -> float:
    """
    Return seconds elapsed since the given Unix timestamp.

    Args:
        timestamp: Unix timestamp (float)

    Returns:
        Elapsed seconds as a float
    """
    return time.time() - timestamp


def minutes_since(timestamp: float) -> float:
    """
    Return minutes elapsed since the given Unix timestamp.

    Args:
        timestamp: Unix timestamp (float)

    Returns:
        Elapsed minutes as a float
    """
    return seconds_since(timestamp) / 60.0


def days_since(timestamp: float) -> float:
    """
    Return days elapsed since the given Unix timestamp.

    Args:
        timestamp: Unix timestamp (float)

    Returns:
        Elapsed days as a float
    """
    return seconds_since(timestamp) / 86400.0


def utcnow_timestamp() -> float:
    """Return current UTC time as a Unix timestamp."""
    return datetime.now(timezone.utc).timestamp()
