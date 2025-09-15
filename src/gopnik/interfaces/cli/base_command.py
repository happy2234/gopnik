"""
Base command class for CLI commands.
"""

import argparse
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

from ...config import GopnikConfig


class BaseCommand(ABC):
    """
    Abstract base class for CLI commands.
    
    Provides common functionality and interface for all CLI commands.
    """
    
    def __init__(self, config: GopnikConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @staticmethod
    @abstractmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the parser."""
        pass
    
    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the command with parsed arguments.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        pass
    
    def validate_file_path(self, path: Path, must_exist: bool = True) -> bool:
        """
        Validate a file path.
        
        Args:
            path: Path to validate
            must_exist: Whether the file must already exist
            
        Returns:
            True if valid, False otherwise
        """
        if must_exist and not path.exists():
            self.logger.error(f"File not found: {path}")
            return False
        
        if must_exist and not path.is_file():
            self.logger.error(f"Path is not a file: {path}")
            return False
        
        if not must_exist:
            # Check if parent directory exists and is writable
            parent = path.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    self.logger.error(f"Cannot create output directory {parent}: {e}")
                    return False
            
            if not parent.is_dir():
                self.logger.error(f"Parent path is not a directory: {parent}")
                return False
        
        return True
    
    def validate_directory_path(self, path: Path, must_exist: bool = True) -> bool:
        """
        Validate a directory path.
        
        Args:
            path: Path to validate
            must_exist: Whether the directory must already exist
            
        Returns:
            True if valid, False otherwise
        """
        if must_exist and not path.exists():
            self.logger.error(f"Directory not found: {path}")
            return False
        
        if must_exist and not path.is_dir():
            self.logger.error(f"Path is not a directory: {path}")
            return False
        
        if not must_exist:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.logger.error(f"Cannot create directory {path}: {e}")
                return False
        
        return True
    
    def format_error(self, message: str, details: Optional[Dict[str, Any]] = None) -> str:
        """
        Format an error message with optional details.
        
        Args:
            message: Main error message
            details: Optional additional details
            
        Returns:
            Formatted error message
        """
        if not details:
            return f"Error: {message}"
        
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        return f"Error: {message} ({detail_str})"
    
    def format_success(self, message: str, details: Optional[Dict[str, Any]] = None) -> str:
        """
        Format a success message with optional details.
        
        Args:
            message: Main success message
            details: Optional additional details
            
        Returns:
            Formatted success message
        """
        if not details:
            return f"Success: {message}"
        
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        return f"Success: {message} ({detail_str})"
    
    def print_json(self, data: Any, indent: int = 2) -> None:
        """Print data as formatted JSON."""
        import json
        print(json.dumps(data, indent=indent, default=str))
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """
        Ask user for confirmation.
        
        Args:
            message: Confirmation message
            default: Default response if user just presses Enter
            
        Returns:
            True if user confirms, False otherwise
        """
        suffix = " [Y/n]" if default else " [y/N]"
        
        try:
            response = input(f"{message}{suffix}: ").strip().lower()
            
            if not response:
                return default
            
            return response in ('y', 'yes', 'true', '1')
            
        except (EOFError, KeyboardInterrupt):
            return False