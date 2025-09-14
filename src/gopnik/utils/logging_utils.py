"""
Logging configuration and utilities.
"""

import logging
import logging.config
from pathlib import Path
from typing import Optional, Dict, Any
import sys


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None,
    include_console: bool = True
) -> None:
    """
    Set up logging configuration for Gopnik.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to write logs to
        format_string: Custom format string for log messages
        include_console: Whether to include console output
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # Create logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': format_string,
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {},
        'loggers': {
            'gopnik': {
                'level': level,
                'handlers': [],
                'propagate': False
            },
            'root': {
                'level': level,
                'handlers': []
            }
        }
    }
    
    # Add console handler if requested
    if include_console:
        config['handlers']['console'] = {
            'class': 'logging.StreamHandler',
            'level': level,
            'formatter': 'standard',
            'stream': sys.stdout
        }
        config['loggers']['gopnik']['handlers'].append('console')
        config['loggers']['root']['handlers'].append('console')
    
    # Add file handler if log file specified
    if log_file:
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        config['handlers']['file'] = {
            'class': 'logging.FileHandler',
            'level': level,
            'formatter': 'standard',
            'filename': str(log_file),
            'mode': 'a'
        }
        config['loggers']['gopnik']['handlers'].append('file')
        config['loggers']['root']['handlers'].append('file')
    
    # Apply configuration
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"gopnik.{name}")


def configure_audit_logging(audit_log_file: Path) -> logging.Logger:
    """
    Configure specialized audit logging.
    
    Args:
        audit_log_file: Path to audit log file
        
    Returns:
        Audit logger instance
    """
    # Ensure audit log directory exists
    audit_log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create audit logger
    audit_logger = logging.getLogger('gopnik.audit')
    audit_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in audit_logger.handlers[:]:
        audit_logger.removeHandler(handler)
    
    # Create file handler for audit logs
    handler = logging.FileHandler(audit_log_file)
    handler.setLevel(logging.INFO)
    
    # Create formatter for audit logs (structured format)
    formatter = logging.Formatter(
        '%(asctime)s - AUDIT - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    audit_logger.addHandler(handler)
    audit_logger.propagate = False
    
    return audit_logger


class StructuredLogger:
    """
    Structured logger for consistent log formatting.
    """
    
    def __init__(self, name: str):
        self.logger = get_logger(name)
    
    def log_operation(self, operation: str, details: Dict[str, Any], 
                     level: str = "INFO") -> None:
        """
        Log an operation with structured details.
        
        Args:
            operation: Operation name
            details: Operation details
            level: Log level
        """
        log_level = getattr(logging, level.upper())
        message = f"Operation: {operation}"
        
        # Add details to message
        if details:
            detail_parts = [f"{k}={v}" for k, v in details.items()]
            message += f" | {' | '.join(detail_parts)}"
        
        self.logger.log(log_level, message)
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error with context information.
        
        Args:
            error: Exception that occurred
            context: Additional context information
        """
        message = f"Error: {type(error).__name__}: {str(error)}"
        
        if context:
            context_parts = [f"{k}={v}" for k, v in context.items()]
            message += f" | Context: {' | '.join(context_parts)}"
        
        self.logger.error(message, exc_info=True)
    
    def log_performance(self, operation: str, duration: float, 
                       additional_metrics: Optional[Dict[str, Any]] = None) -> None:
        """
        Log performance metrics for an operation.
        
        Args:
            operation: Operation name
            duration: Duration in seconds
            additional_metrics: Additional performance metrics
        """
        message = f"Performance: {operation} | duration={duration:.3f}s"
        
        if additional_metrics:
            metric_parts = [f"{k}={v}" for k, v in additional_metrics.items()]
            message += f" | {' | '.join(metric_parts)}"
        
        self.logger.info(message)