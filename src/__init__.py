"""
Gopnik - AI Toolkit for Forensic-Grade Visual & Textual Deidentification
"""

__version__ = "0.1.0"
__author__ = "Gaurav Kumar"
__email__ = "your.email@example.com"

from .core.config import Config
from .core.exceptions import GopnikError
from .core.logger import get_logger, setup_logging

__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "Config",
    "get_logger",
    "setup_logging",
    "GopnikError",
]
