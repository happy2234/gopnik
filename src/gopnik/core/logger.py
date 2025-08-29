"""Logging configuration for Gopnik."""

import logging
import sys
from pathlib import Path
from typing import Optional

from loguru import logger as loguru_logger

from .config import config


def setup_logging(
    log_level: str = config.LOG_LEVEL,
    log_file: Optional[Path] = None,
) -> None:
    """Setup logging configuration."""

    # Create logs directory
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    loguru_logger.remove()

    # Add console handler
    loguru_logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # Add file handler
    if log_file is None:
        log_file = config.LOGS_DIR / "gopnik.log"

    loguru_logger.add(
        str(log_file),
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )


def get_logger(name: str) -> loguru_logger:
    """Get logger instance."""
    return loguru_logger.bind(name=name)


# Initialize logging
setup_logging()
