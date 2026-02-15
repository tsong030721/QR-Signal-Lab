"""
Global configurations for a logger
"""
import logging
from typing import Optional

levels = [logging.WARNING, logging.INFO, logging.DEBUG]

def configure(level: int = 0) -> None:
    """
    Configure root logger at application startup.
    """
    logging.basicConfig(
        level=levels[level],
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def get(name: Optional[str] = None) -> logging.Logger:
    """
    Get a module-level logger.
    """
    return logging.getLogger(name)