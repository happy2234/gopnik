"""
Error handling and reporting utilities for CLI.
"""

import sys
import traceback
import logging
from typing import Optional, Dict, Any
from pathlib import Path


class CLIError(Exception):
    """Base exception for CLI-specific errors."""
    
    def __init__(self, message: str, exit_code: int = 1, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
        self.details = details or {}


class FileNotFoundError(CLIError):
    """Error when a required file is not found."""
    
    def __init__(self, file_path: Path, file_type: str = "file"):
        message = f"{file_type.capitalize()} not found: {file_path}"
        super().__init__(message, exit_code=2)
        self.file_path = file_path
        self.file_type = file_type


class InvalidArgumentError(CLIError):
    """Error when command line arguments are invalid."""
    
    def __init__(self, argument: str, reason: str):
        message = f"Invalid argument '{argument}': {reason}"
        super().__init__(message, exit_code=2)
        self.argument = argument
        self.reason = reason


class ProcessingError(CLIError):
    """Error during document processing."""
    
    def __init__(self, message: str, document_path: Optional[Path] = None):
        super().__init__(message, exit_code=3)
        self.document_path = document_path


class ProfileError(CLIError):
    """Error related to profile operations."""
    
    def __init__(self, message: str, profile_name: Optional[str] = None):
        super().__init__(message, exit_code=4)
        self.profile_name = profile_name


class ValidationError(CLIError):
    """Error during document validation."""
    
    def __init__(self, message: str, document_path: Optional[Path] = None):
        super().__init__(message, exit_code=5)
        self.document_path = document_path


class ErrorReporter:
    """
    Centralized error reporting for CLI operations.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def report_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> int:
        """
        Report an error and return appropriate exit code.
        
        Args:
            error: Exception that occurred
            context: Additional context information
            
        Returns:
            Exit code for the application
        """
        context = context or {}
        
        if isinstance(error, CLIError):
            return self._report_cli_error(error, context)
        elif isinstance(error, KeyboardInterrupt):
            return self._report_keyboard_interrupt(context)
        elif isinstance(error, PermissionError):
            return self._report_permission_error(error, context)
        elif isinstance(error, OSError):
            return self._report_os_error(error, context)
        else:
            return self._report_unexpected_error(error, context)
    
    def _report_cli_error(self, error: CLIError, context: Dict[str, Any]) -> int:
        """Report a CLI-specific error."""
        self.logger.error(error.message)
        
        # Add details if available
        if error.details:
            for key, value in error.details.items():
                self.logger.debug(f"  {key}: {value}")
        
        # Add context if available
        if context:
            for key, value in context.items():
                self.logger.debug(f"  {key}: {value}")
        
        return error.exit_code
    
    def _report_keyboard_interrupt(self, context: Dict[str, Any]) -> int:
        """Report keyboard interrupt (Ctrl+C)."""
        self.logger.info("Operation cancelled by user")
        return 130  # Standard exit code for SIGINT
    
    def _report_permission_error(self, error: PermissionError, context: Dict[str, Any]) -> int:
        """Report permission-related errors."""
        self.logger.error(f"Permission denied: {error}")
        
        # Provide helpful suggestions
        if hasattr(error, 'filename') and error.filename:
            file_path = Path(error.filename)
            if file_path.exists():
                self.logger.info(f"Check file permissions for: {file_path}")
            else:
                self.logger.info(f"Check directory permissions for: {file_path.parent}")
        
        return 13  # Permission denied exit code
    
    def _report_os_error(self, error: OSError, context: Dict[str, Any]) -> int:
        """Report OS-related errors."""
        self.logger.error(f"System error: {error}")
        
        # Provide specific guidance for common OS errors
        if error.errno == 2:  # No such file or directory
            self.logger.info("Check that all file paths are correct and files exist")
        elif error.errno == 13:  # Permission denied
            self.logger.info("Check file and directory permissions")
        elif error.errno == 28:  # No space left on device
            self.logger.info("Free up disk space and try again")
        elif error.errno == 36:  # File name too long
            self.logger.info("Use shorter file names or paths")
        
        return 1
    
    def _report_unexpected_error(self, error: Exception, context: Dict[str, Any]) -> int:
        """Report unexpected errors with full traceback."""
        self.logger.error(f"Unexpected error: {error}")
        
        # Log full traceback for debugging
        self.logger.debug("Full traceback:")
        self.logger.debug(traceback.format_exc())
        
        # Provide general guidance
        self.logger.info("This appears to be an unexpected error. Please report this issue.")
        if context:
            self.logger.info("Include the following context in your report:")
            for key, value in context.items():
                self.logger.info(f"  {key}: {value}")
        
        return 1
    
    def format_user_friendly_error(self, error: Exception, format_type: str = 'text') -> str:
        """
        Format error message in a user-friendly way.
        
        Args:
            error: Exception to format
            format_type: Output format ('text' or 'json')
            
        Returns:
            Formatted error message
        """
        if format_type == 'json':
            import json
            error_data = {
                'error': True,
                'type': type(error).__name__,
                'message': str(error)
            }
            
            if isinstance(error, CLIError):
                error_data['exit_code'] = error.exit_code
                error_data['details'] = error.details
            
            return json.dumps(error_data, indent=2)
        
        else:  # text format
            if isinstance(error, CLIError):
                return f"Error: {error.message}"
            else:
                return f"Error: {str(error)}"
    
    def suggest_solutions(self, error: Exception) -> list[str]:
        """
        Suggest possible solutions for common errors.
        
        Args:
            error: Exception that occurred
            
        Returns:
            List of suggested solutions
        """
        suggestions = []
        
        if isinstance(error, FileNotFoundError):
            suggestions.extend([
                "Check that the file path is correct",
                "Verify the file exists and is accessible",
                "Use absolute paths if relative paths are not working"
            ])
        
        elif isinstance(error, InvalidArgumentError):
            suggestions.extend([
                "Check the command syntax with --help",
                "Verify all required arguments are provided",
                "Check argument values are in the correct format"
            ])
        
        elif isinstance(error, ProcessingError):
            suggestions.extend([
                "Check that the document format is supported",
                "Verify the document is not corrupted",
                "Try with a different redaction profile",
                "Check available disk space for output files"
            ])
        
        elif isinstance(error, ProfileError):
            suggestions.extend([
                "List available profiles with 'gopnik profile list'",
                "Check profile syntax with 'gopnik profile validate'",
                "Create a new profile if needed"
            ])
        
        elif isinstance(error, ValidationError):
            suggestions.extend([
                "Check that the audit log corresponds to the document",
                "Verify audit log format is correct",
                "Ensure document has not been modified since processing"
            ])
        
        elif isinstance(error, PermissionError):
            suggestions.extend([
                "Check file and directory permissions",
                "Run with appropriate user privileges",
                "Ensure output directory is writable"
            ])
        
        return suggestions


def handle_cli_exception(func):
    """
    Decorator to handle CLI exceptions gracefully.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function that handles exceptions
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            reporter = ErrorReporter()
            exit_code = reporter.report_error(e)
            sys.exit(exit_code)
    
    return wrapper


def validate_file_exists(file_path: Path, file_type: str = "file") -> None:
    """
    Validate that a file exists, raising appropriate error if not.
    
    Args:
        file_path: Path to validate
        file_type: Type of file for error message
        
    Raises:
        FileNotFoundError: If file does not exist
    """
    if not file_path.exists():
        raise FileNotFoundError(file_path, file_type)


def validate_directory_exists(dir_path: Path) -> None:
    """
    Validate that a directory exists, raising appropriate error if not.
    
    Args:
        dir_path: Directory path to validate
        
    Raises:
        FileNotFoundError: If directory does not exist
    """
    if not dir_path.exists():
        raise FileNotFoundError(dir_path, "directory")
    
    if not dir_path.is_dir():
        raise InvalidArgumentError(str(dir_path), "path is not a directory")


def validate_output_path(output_path: Path, force: bool = False) -> None:
    """
    Validate output path, checking for overwrites.
    
    Args:
        output_path: Output path to validate
        force: Whether to allow overwriting existing files
        
    Raises:
        InvalidArgumentError: If output path is invalid
    """
    if output_path.exists() and not force:
        raise InvalidArgumentError(
            str(output_path), 
            "output file exists (use --force to overwrite)"
        )
    
    # Check if parent directory exists and is writable
    parent = output_path.parent
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise InvalidArgumentError(
                str(output_path),
                f"cannot create output directory: {e}"
            )
    
    if not parent.is_dir():
        raise InvalidArgumentError(
            str(output_path),
            "parent path is not a directory"
        )