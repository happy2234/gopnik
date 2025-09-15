"""
Process command implementation for single document processing.
"""

import argparse
from pathlib import Path
from typing import Optional

from ..base_command import BaseCommand
from ..progress import create_spinner
from ..errors import ProcessingError, ProfileError, validate_file_exists, validate_output_path
from ....core.processor import DocumentProcessor
from ....models.profiles import RedactionProfile, ProfileManager


class ProcessCommand(BaseCommand):
    """Command for processing a single document."""
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add process command arguments."""
        
        # Required arguments
        parser.add_argument(
            'input',
            type=Path,
            help='Input document path'
        )
        
        # Optional arguments
        parser.add_argument(
            '--output', '-o',
            type=Path,
            help='Output document path (default: <input>_redacted.<ext>)'
        )
        
        parser.add_argument(
            '--profile', '-p',
            type=str,
            default='default',
            help='Redaction profile name (default: default)'
        )
        
        parser.add_argument(
            '--profile-file',
            type=Path,
            help='Path to custom profile file'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite output file if it exists'
        )
        
        parser.add_argument(
            '--no-audit',
            action='store_true',
            help='Skip audit log creation'
        )
        
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the process command."""
        
        # Validate input file
        try:
            validate_file_exists(args.input, "document")
        except Exception as e:
            self.logger.error(str(e))
            return 1
        
        # Determine output path
        output_path = args.output
        if not output_path:
            stem = args.input.stem
            suffix = args.input.suffix
            output_path = args.input.parent / f"{stem}_redacted{suffix}"
        
        # Validate output path
        try:
            # Check if output exists and handle --force
            if output_path.exists() and not args.force:
                if not self.confirm_action(f"Output file {output_path} exists. Overwrite?"):
                    self.logger.info("Operation cancelled by user")
                    return 0
            
            validate_output_path(output_path, args.force)
        except Exception as e:
            self.logger.error(str(e))
            return 1
        
        # Load redaction profile
        try:
            profile = self._load_profile(args)
        except Exception as e:
            raise ProfileError(f"Failed to load profile: {e}")
        
        # Dry run mode
        if args.dry_run:
            return self._execute_dry_run(args, profile, output_path)
        
        # Execute processing
        return self._execute_processing(args, profile, output_path)
    
    def _load_profile(self, args: argparse.Namespace) -> RedactionProfile:
        """Load redaction profile from arguments."""
        
        if args.profile_file:
            # Load from custom file
            if not self.validate_file_path(args.profile_file, must_exist=True):
                raise ValueError(f"Profile file not found: {args.profile_file}")
            
            if args.profile_file.suffix.lower() in ['.yaml', '.yml']:
                return RedactionProfile.from_yaml(args.profile_file)
            elif args.profile_file.suffix.lower() == '.json':
                return RedactionProfile.from_json(args.profile_file)
            else:
                raise ValueError(f"Unsupported profile file format: {args.profile_file.suffix}")
        
        else:
            # Load by name using ProfileManager
            profile_manager = ProfileManager()
            return profile_manager.load_profile(args.profile)
    
    def _execute_dry_run(self, args: argparse.Namespace, profile: RedactionProfile, 
                        output_path: Path) -> int:
        """Execute dry run mode."""
        
        self.logger.info("=== DRY RUN MODE ===")
        self.logger.info(f"Input: {args.input}")
        self.logger.info(f"Output: {output_path}")
        self.logger.info(f"Profile: {profile.name}")
        
        # Show profile details
        if args.format == 'json':
            self.print_json({
                'mode': 'dry_run',
                'input': str(args.input),
                'output': str(output_path),
                'profile': {
                    'name': profile.name,
                    'description': profile.description,
                    'pii_types': [pii_type.value for pii_type in profile.pii_types],
                    'redaction_style': profile.redaction_style.value
                }
            })
        else:
            print(f"\nProfile Details:")
            print(f"  Name: {profile.name}")
            print(f"  Description: {profile.description}")
            print(f"  PII Types: {', '.join(pii_type.value for pii_type in profile.pii_types)}")
            print(f"  Redaction Style: {profile.redaction_style.value}")
        
        self.logger.info("Dry run completed. Use without --dry-run to execute.")
        return 0
    
    def _execute_processing(self, args: argparse.Namespace, profile: RedactionProfile,
                          output_path: Path) -> int:
        """Execute actual document processing."""
        
        try:
            # Initialize processor
            processor = DocumentProcessor(self.config)
            
            # TODO: Set up AI engine when available
            # processor.set_ai_engine(ai_engine)
            
            self.logger.info(f"Processing document: {args.input}")
            self.logger.info(f"Using profile: {profile.name}")
            
            # Create spinner for progress indication
            spinner = create_spinner(
                f"Processing {args.input.name}...", 
                args.format == 'text'
            )
            
            if spinner:
                spinner.start()
            
            try:
                # Process document
                result = processor.process_document(args.input, profile)
            finally:
                if spinner:
                    spinner.stop()
            
            # Move output to desired location if different
            if result.output_path and result.output_path != output_path:
                result.output_path.rename(output_path)
                result.output_path = output_path
            
            # Report results
            if args.format == 'json':
                self.print_json({
                    'status': 'success' if result.success else 'failed',
                    'input': str(args.input),
                    'output': str(output_path) if result.success else None,
                    'detections_found': len(result.detections) if result.detections else 0,
                    'processing_time': result.metrics.total_time if result.metrics else None,
                    'error': result.error_message if not result.success else None
                })
            else:
                if result.success:
                    print(self.format_success(
                        "Document processed successfully",
                        {
                            'output': output_path,
                            'detections': len(result.detections) if result.detections else 0,
                            'time': f"{result.metrics.total_time:.2f}s" if result.metrics else "N/A"
                        }
                    ))
                else:
                    print(self.format_error(
                        "Document processing failed",
                        {'error': result.error_message}
                    ))
            
            return 0 if result.success else 1
            
        except Exception as e:
            if args.format == 'json':
                self.print_json({
                    'status': 'error',
                    'error': str(e)
                })
            else:
                print(self.format_error(f"Processing failed: {e}"))
            
            return 1