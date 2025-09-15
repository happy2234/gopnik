"""
Main CLI entry point for Gopnik deidentification system.

Provides comprehensive command-line interface for document processing,
validation, batch operations, and profile management.
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from ...config import GopnikConfig
from ...utils.logging_utils import setup_logging
from .commands import ProcessCommand, ValidateCommand, BatchCommand, ProfileCommand


class GopnikCLI:
    """
    Main CLI application class that handles command parsing and execution.
    """
    
    def __init__(self):
        self.config = GopnikConfig()
        self.logger = None  # Will be initialized after parsing log level
        
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser with all subcommands."""
        
        # Main parser
        parser = argparse.ArgumentParser(
            prog='gopnik',
            description='Gopnik - Forensic-grade document deidentification toolkit',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Process a single document
  gopnik process document.pdf --profile healthcare --output redacted.pdf
  
  # Process all documents in a directory
  gopnik batch /path/to/docs --profile default --recursive --progress
  
  # Validate document integrity
  gopnik validate document.pdf --audit-dir /audit/logs --verify-signatures
  
  # Profile management
  gopnik profile list --verbose
  gopnik profile show healthcare
  gopnik profile create --name custom --based-on default --pii-types name email phone
  gopnik profile validate custom
  
  # Dry run to see what would be processed
  gopnik process document.pdf --profile healthcare --dry-run
  gopnik batch /docs --profile default --dry-run --format json

Supported document formats: PDF, PNG, JPG, JPEG, TIFF, BMP
Supported profile formats: YAML, JSON

For detailed help on a specific command:
  gopnik <command> --help

For more information, visit: https://github.com/your-org/gopnik
            """
        )
        
        # Global arguments
        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0.0'
        )
        
        parser.add_argument(
            '--config',
            type=Path,
            help='Path to configuration file (default: config/default.yaml)'
        )
        
        parser.add_argument(
            '--log-level',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='INFO',
            help='Set logging level (default: INFO)'
        )
        
        parser.add_argument(
            '--log-file',
            type=Path,
            help='Path to log file (default: stderr)'
        )
        
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Suppress all output except errors'
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        
        # Create subparsers
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )
        
        # Process command
        process_parser = subparsers.add_parser(
            'process',
            help='Process a single document for PII redaction',
            description='Process a single document to detect and redact PII according to the specified profile.',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Basic processing with default profile
  gopnik process document.pdf
  
  # Use specific profile and output location
  gopnik process document.pdf --profile healthcare --output /secure/redacted.pdf
  
  # Use custom profile file
  gopnik process document.pdf --profile-file /profiles/custom.yaml
  
  # Dry run to see what would be processed
  gopnik process document.pdf --profile healthcare --dry-run
  
  # Force overwrite existing output
  gopnik process document.pdf --output existing.pdf --force
  
  # JSON output for automation
  gopnik process document.pdf --format json
            """
        )
        ProcessCommand.add_arguments(process_parser)
        
        # Batch command
        batch_parser = subparsers.add_parser(
            'batch',
            help='Process multiple documents in a directory',
            description='Process all supported documents in a directory for PII redaction.',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Process all documents in a directory
  gopnik batch /path/to/documents --profile default
  
  # Recursive processing with progress bar
  gopnik batch /path/to/documents --recursive --progress --profile healthcare
  
  # Process only PDF files
  gopnik batch /documents --pattern "*.pdf" --profile default
  
  # Limit number of files and continue on errors
  gopnik batch /documents --max-files 100 --continue-on-error
  
  # Dry run to see what would be processed
  gopnik batch /documents --dry-run --recursive
  
  # Custom output directory
  gopnik batch /input --output /output --profile healthcare
            """
        )
        BatchCommand.add_arguments(batch_parser)
        
        # Validate command
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate document integrity using audit trail',
            description='Verify document integrity and audit trail authenticity.',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Validate with explicit audit log
  gopnik validate document.pdf audit.json
  
  # Auto-find audit log in same directory
  gopnik validate document.pdf
  
  # Search for audit log in specific directory
  gopnik validate document.pdf --audit-dir /audit/logs
  
  # Strict validation with signature verification
  gopnik validate document.pdf --strict --verify-signatures
  
  # Verbose output with detailed information
  gopnik validate document.pdf --verbose
  
  # JSON output for automation
  gopnik validate document.pdf --format json
            """
        )
        ValidateCommand.add_arguments(validate_parser)
        
        # Profile command
        profile_parser = subparsers.add_parser(
            'profile',
            help='Manage redaction profiles',
            description='Create, list, edit, and manage redaction profiles.',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # List all available profiles
  gopnik profile list
  
  # List profiles with detailed information
  gopnik profile list --verbose --format json
  
  # Show specific profile details
  gopnik profile show healthcare
  
  # Create new profile from scratch
  gopnik profile create --name custom --description "Custom profile" \\
    --pii-types name email phone --redaction-style solid
  
  # Create profile based on existing one
  gopnik profile create --name strict-healthcare --based-on healthcare \\
    --description "Strict healthcare profile"
  
  # Edit existing profile
  gopnik profile edit healthcare --add-pii-types ssn id_number \\
    --redaction-style blur
  
  # Validate profile configuration
  gopnik profile validate healthcare
  
  # Delete profile (with confirmation)
  gopnik profile delete old-profile
  
  # Force delete without confirmation
  gopnik profile delete old-profile --force
            """
        )
        ProfileCommand.add_arguments(profile_parser)
        
        return parser
    
    def setup_logging_from_args(self, args: argparse.Namespace) -> None:
        """Setup logging based on command line arguments."""
        
        # Determine log level
        log_level = args.log_level
        if args.quiet:
            log_level = 'ERROR'
        elif args.verbose:
            log_level = 'DEBUG'
        
        # Setup logging
        setup_logging(
            level=log_level,
            log_file=args.log_file,
            format_type='cli'
        )
        
        self.logger = logging.getLogger(__name__)
        
        if args.verbose:
            self.logger.debug(f"Logging initialized at {log_level} level")
            if args.log_file:
                self.logger.debug(f"Logging to file: {args.log_file}")
    
    def load_config_from_args(self, args: argparse.Namespace) -> None:
        """Load configuration based on command line arguments."""
        
        if args.config:
            if not args.config.exists():
                self.logger.error(f"Configuration file not found: {args.config}")
                sys.exit(1)
            
            try:
                self.config = GopnikConfig.from_file(args.config)
                self.logger.debug(f"Configuration loaded from: {args.config}")
            except Exception as e:
                self.logger.error(f"Failed to load configuration: {e}")
                sys.exit(1)
        else:
            # Use default configuration
            self.logger.debug("Using default configuration")
    
    def validate_arguments(self, args: argparse.Namespace) -> bool:
        """Validate parsed arguments for consistency and requirements."""
        
        if not args.command:
            self.logger.error("No command specified. Use --help for usage information.")
            return False
        
        # Command-specific validation will be handled by individual command classes
        return True
    
    def execute_command(self, args: argparse.Namespace) -> int:
        """Execute the specified command with parsed arguments."""
        
        try:
            if args.command == 'process':
                command = ProcessCommand(self.config)
                return command.execute(args)
            
            elif args.command == 'batch':
                command = BatchCommand(self.config)
                return command.execute(args)
            
            elif args.command == 'validate':
                command = ValidateCommand(self.config)
                return command.execute(args)
            
            elif args.command == 'profile':
                command = ProfileCommand(self.config)
                return command.execute(args)
            
            else:
                self.logger.error(f"Unknown command: {args.command}")
                return 1
                
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            return 130  # Standard exit code for SIGINT
        
        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.exception("Full traceback:")
            return 1
    
    def run(self, argv: Optional[List[str]] = None) -> int:
        """
        Main entry point for CLI application.
        
        Args:
            argv: Command line arguments (default: sys.argv[1:])
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        
        # Parse arguments
        parser = self.create_parser()
        
        if argv is None:
            argv = sys.argv[1:]
        
        # Handle case where no arguments are provided
        if not argv:
            parser.print_help()
            return 0
        
        try:
            args = parser.parse_args(argv)
        except SystemExit as e:
            # argparse calls sys.exit() on error or --help
            return e.code if e.code is not None else 0
        
        # Setup logging first
        self.setup_logging_from_args(args)
        
        # Load configuration
        self.load_config_from_args(args)
        
        # Validate arguments
        if not self.validate_arguments(args):
            return 1
        
        # Execute command
        return self.execute_command(args)


def main() -> int:
    """Main entry point for the gopnik CLI."""
    cli = GopnikCLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())