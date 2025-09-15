"""
Command-line interface for Gopnik deidentification system.

Provides forensic-grade offline processing capabilities.
"""

from .main import GopnikCLI, main
from .base_command import BaseCommand
from .commands import ProcessCommand, BatchCommand, ValidateCommand, ProfileCommand

__all__ = [
    'GopnikCLI',
    'main',
    'BaseCommand',
    'ProcessCommand',
    'BatchCommand',
    'ValidateCommand',
    'ProfileCommand'
]