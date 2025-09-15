"""
Batch command implementation for processing multiple documents.
"""

import argparse
from pathlib import Path
from typing import List
import time
import sys

from ..base_command import BaseCommand
from ..progress import create_progress_bar
from ....core.processor import DocumentProcessor
from ....models.profiles import RedactionProfile, ProfileManager


class BatchCommand(BaseCommand):
    """Command for batch processing multiple documents."""
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add batch command arguments."""
        
        # Required arguments
        parser.add_argument(
            'input_dir',
            type=Path,
            help='Input directory containing documents to process'
        )
        
        # Optional arguments
        parser.add_argument(
            '--output', '-o',
            type=Path,
            help='Output directory (default: <input_dir>_redacted)'
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
            '--recursive', '-r',
            action='store_true',
            help='Process subdirectories recursively'
        )
        
        parser.add_argument(
            '--pattern',
            type=str,
            help='File pattern to match (e.g., "*.pdf")'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite output files if they exist'
        )
        
        parser.add_argument(
            '--continue-on-error',
            action='store_true',
            help='Continue processing other files if one fails'
        )
        
        parser.add_argument(
            '--max-files',
            type=int,
            help='Maximum number of files to process'
        )
        
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        
        parser.add_argument(
            '--progress',
            action='store_true',
            help='Show progress bar during processing'
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the batch command."""
        
        # Validate input directory
        if not self.validate_directory_path(args.input_dir, must_exist=True):
            return 1
        
        # Determine output directory
        output_dir = args.output
        if not output_dir:
            output_dir = args.input_dir.parent / f"{args.input_dir.name}_redacted"
        
        # Validate output directory
        if not self.validate_directory_path(output_dir, must_exist=False):
            return 1
        
        # Load redaction profile
        try:
            profile = self._load_profile(args)
        except Exception as e:
            self.logger.error(f"Failed to load profile: {e}")
            return 1
        
        # Find files to process
        try:
            files_to_process = self._find_files(args)
        except Exception as e:
            self.logger.error(f"Failed to find files: {e}")
            return 1
        
        if not files_to_process:
            self.logger.warning(f"No supported files found in {args.input_dir}")
            return 0
        
        # Apply max files limit
        if args.max_files and len(files_to_process) > args.max_files:
            files_to_process = files_to_process[:args.max_files]
            self.logger.info(f"Limited to {args.max_files} files")
        
        # Dry run mode
        if args.dry_run:
            return self._execute_dry_run(args, profile, files_to_process, output_dir)
        
        # Execute batch processing
        return self._execute_batch_processing(args, profile, files_to_process, output_dir)
    
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
    
    def _find_files(self, args: argparse.Namespace) -> List[Path]:
        """Find files to process based on arguments."""
        
        files = []
        
        if args.recursive:
            pattern = args.pattern or '*'
            files = list(args.input_dir.rglob(pattern))
        else:
            pattern = args.pattern or '*'
            files = list(args.input_dir.glob(pattern))
        
        # Filter to only files (not directories)
        files = [f for f in files if f.is_file()]
        
        # Filter to supported formats
        # TODO: Get supported formats from DocumentAnalyzer
        supported_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp'}
        files = [f for f in files if f.suffix.lower() in supported_extensions]
        
        # Sort for consistent ordering
        files.sort()
        
        return files
    
    def _execute_dry_run(self, args: argparse.Namespace, profile: RedactionProfile,
                        files: List[Path], output_dir: Path) -> int:
        """Execute dry run mode."""
        
        self.logger.info("=== BATCH DRY RUN MODE ===")
        self.logger.info(f"Input Directory: {args.input_dir}")
        self.logger.info(f"Output Directory: {output_dir}")
        self.logger.info(f"Profile: {profile.name}")
        self.logger.info(f"Files Found: {len(files)}")
        
        if args.format == 'json':
            self.print_json({
                'mode': 'batch_dry_run',
                'input_directory': str(args.input_dir),
                'output_directory': str(output_dir),
                'profile': profile.name,
                'files_found': len(files),
                'files': [str(f) for f in files[:10]],  # Show first 10
                'truncated': len(files) > 10
            })
        else:
            print(f"\nFiles to process ({len(files)}):")
            for i, file_path in enumerate(files[:10], 1):
                rel_path = file_path.relative_to(args.input_dir)
                print(f"  {i:3d}. {rel_path}")
            
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more files")
        
        self.logger.info("Dry run completed. Use without --dry-run to execute.")
        return 0
    
    def _execute_batch_processing(self, args: argparse.Namespace, profile: RedactionProfile,
                                 files: List[Path], output_dir: Path) -> int:
        """Execute actual batch processing."""
        
        try:
            # Initialize processor
            processor = DocumentProcessor(self.config)
            
            # TODO: Set up AI engine when available
            # processor.set_ai_engine(ai_engine)
            
            self.logger.info(f"Starting batch processing of {len(files)} files")
            self.logger.info(f"Using profile: {profile.name}")
            
            # Process files
            successful = 0
            failed = 0
            start_time = time.time()
            
            # Create progress bar if requested
            progress_bar = create_progress_bar(
                len(files), 
                "Processing documents", 
                args.progress and args.format == 'text'
            )
            
            for i, file_path in enumerate(files, 1):
                rel_path = file_path.relative_to(args.input_dir)
                
                # Update progress bar or show text progress
                if progress_bar:
                    progress_bar.update(description=f"Processing {rel_path.name}")
                elif args.format == 'text' and not args.progress:
                    print(f"Processing {i}/{len(files)}: {rel_path}")
                
                try:
                    # Determine output path
                    output_path = output_dir / rel_path
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Check if output exists
                    if output_path.exists() and not args.force:
                        self.logger.warning(f"Skipping {rel_path} - output exists (use --force to overwrite)")
                        continue
                    
                    # Process document
                    result = processor.process_document(file_path, profile)
                    
                    if result.success:
                        # Move output to correct location
                        if result.output_path and result.output_path != output_path:
                            result.output_path.rename(output_path)
                        
                        successful += 1
                        
                        if args.format == 'text' and not progress_bar:
                            detections = len(result.detections) if result.detections else 0
                            time_taken = result.metrics.total_time if result.metrics else 0
                            print(f"  ✓ Success ({detections} detections, {time_taken:.2f}s)")
                    
                    else:
                        failed += 1
                        
                        if args.format == 'text' and not progress_bar:
                            print(f"  ✗ Failed: {result.error_message}")
                        
                        if not args.continue_on_error:
                            if progress_bar:
                                progress_bar.finish()
                            self.logger.error("Stopping batch processing due to error")
                            break
                
                except Exception as e:
                    failed += 1
                    
                    if args.format == 'text' and not progress_bar:
                        print(f"  ✗ Error: {e}")
                    
                    if not args.continue_on_error:
                        if progress_bar:
                            progress_bar.finish()
                        self.logger.error(f"Stopping batch processing due to error: {e}")
                        break
            
            # Finish progress bar
            if progress_bar:
                progress_bar.finish()
            
            # Report final results
            total_time = time.time() - start_time
            
            if args.format == 'json':
                self.print_json({
                    'status': 'completed',
                    'total_files': len(files),
                    'successful': successful,
                    'failed': failed,
                    'total_time': total_time,
                    'output_directory': str(output_dir)
                })
            else:
                print(f"\nBatch processing completed:")
                print(f"  Total files: {len(files)}")
                print(f"  Successful: {successful}")
                print(f"  Failed: {failed}")
                print(f"  Total time: {total_time:.2f}s")
                print(f"  Output directory: {output_dir}")
            
            return 0 if failed == 0 else 1
            
        except Exception as e:
            if args.format == 'json':
                self.print_json({
                    'status': 'error',
                    'error': str(e)
                })
            else:
                print(self.format_error(f"Batch processing failed: {e}"))
            
            return 1