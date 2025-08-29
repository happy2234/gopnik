"""Test logging module."""

from pathlib import Path

import pytest

from gopnik.core.logger import get_logger, setup_logging


def test_get_logger():
    """Test logger creation."""
    logger = get_logger("test")
    assert logger is not None


def test_setup_logging(tmp_path):
    """Test logging setup."""
    log_file = tmp_path / "test.log"
    setup_logging(log_level="DEBUG", log_file=log_file)

    logger = get_logger("test_setup")
    logger.info("Test message")

    assert log_file.exists()
