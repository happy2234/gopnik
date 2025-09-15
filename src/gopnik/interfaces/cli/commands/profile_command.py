"""
Profile command implementation for redaction profile management.
"""

import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from ..base_command import BaseCommand
from ....models.profiles import RedactionProfile, RedactionStyle, ProfileManager
from ....models.pii import PIIType


class ProfileCommand(BaseCommand):
    """Command for managing redaction profiles."""
    
    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """Add profile command arguments."""
        
        # Create subparsers for profile operations
        subparsers = parser.add_subparsers(
            dest='profile_action',
            help='Profile management actions',
            metavar='ACTION'
        )
        
        # List profiles
        list_parser = subparsers.add_parser(
            'list',
            help='List available profiles'
        )
        list_parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        list_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Show detailed profile information'
        )
        
        # Show profile details
        show_parser = subparsers.add_parser(
            'show',
            help='Show profile details'
        )
        show_parser.add_argument(
            'name',
            help='Profile name to show'
        )
        show_parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        
        # Create new profile
        create_parser = subparsers.add_parser(
            'create',
            help='Create a new profile'
        )
        create_parser.add_argument(
            '--name',
            required=True,
            help='Profile name'
        )
        create_parser.add_argument(
            '--description',
            help='Profile description'
        )
        create_parser.add_argument(
            '--based-on',
            help='Base profile to copy from'
        )
        create_parser.add_argument(
            '--pii-types',
            nargs='+',
            help='PII types to detect (e.g., name email phone)'
        )
        create_parser.add_argument(
            '--redaction-style',
            choices=['solid', 'pattern', 'blur'],
            help='Redaction style'
        )
        create_parser.add_argument(
            '--output',
            type=Path,
            help='Output file path (default: profiles/<name>.yaml)'
        )
        
        # Edit existing profile
        edit_parser = subparsers.add_parser(
            'edit',
            help='Edit an existing profile'
        )
        edit_parser.add_argument(
            'name',
            help='Profile name to edit'
        )
        edit_parser.add_argument(
            '--description',
            help='New profile description'
        )
        edit_parser.add_argument(
            '--add-pii-types',
            nargs='+',
            help='PII types to add'
        )
        edit_parser.add_argument(
            '--remove-pii-types',
            nargs='+',
            help='PII types to remove'
        )
        edit_parser.add_argument(
            '--redaction-style',
            choices=['solid', 'pattern', 'blur'],
            help='New redaction style'
        )
        
        # Validate profile
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate a profile'
        )
        validate_parser.add_argument(
            'profile',
            help='Profile name or file path to validate'
        )
        validate_parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (default: text)'
        )
        
        # Delete profile
        delete_parser = subparsers.add_parser(
            'delete',
            help='Delete a profile'
        )
        delete_parser.add_argument(
            'name',
            help='Profile name to delete'
        )
        delete_parser.add_argument(
            '--force',
            action='store_true',
            help='Delete without confirmation'
        )
    
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the profile command."""
        
        if not args.profile_action:
            self.logger.error("No profile action specified. Use --help for usage information.")
            return 1
        
        try:
            if args.profile_action == 'list':
                return self._list_profiles(args)
            
            elif args.profile_action == 'show':
                return self._show_profile(args)
            
            elif args.profile_action == 'create':
                return self._create_profile(args)
            
            elif args.profile_action == 'edit':
                return self._edit_profile(args)
            
            elif args.profile_action == 'validate':
                return self._validate_profile(args)
            
            elif args.profile_action == 'delete':
                return self._delete_profile(args)
            
            else:
                self.logger.error(f"Unknown profile action: {args.profile_action}")
                return 1
                
        except Exception as e:
            self.logger.error(f"Profile operation failed: {e}")
            return 1
    
    def _list_profiles(self, args: argparse.Namespace) -> int:
        """List available profiles."""
        
        try:
            # Get available profiles
            profile_manager = ProfileManager()
            profile_names = profile_manager.list_profiles()
            profiles = {name: self._find_profile_path(name) for name in profile_names}
            
            if args.format == 'json':
                profile_data = []
                for name, path in profiles.items():
                    try:
                        profile_manager = ProfileManager()
                        profile = profile_manager.load_profile(name, resolve_inheritance=False)
                        
                        # Get enabled PII types
                        enabled_pii_types = []
                        for pii_type, enabled in profile.visual_rules.items():
                            if enabled:
                                enabled_pii_types.append(pii_type)
                        for pii_type, enabled in profile.text_rules.items():
                            if enabled:
                                enabled_pii_types.append(pii_type)
                        
                        profile_data.append({
                            'name': name,
                            'path': str(path) if path else 'unknown',
                            'description': profile.description,
                            'pii_types': enabled_pii_types,
                            'redaction_style': profile.redaction_style.value
                        })
                    except Exception as e:
                        profile_data.append({
                            'name': name,
                            'path': str(path) if path else 'unknown',
                            'error': str(e)
                        })
                
                self.print_json(profile_data)
            
            else:
                if not profiles:
                    print("No profiles found.")
                    return 0
                
                print(f"Available Profiles ({len(profiles)}):")
                print()
                
                for name, path in profiles.items():
                    try:
                        profile_manager = ProfileManager()
                        profile = profile_manager.load_profile(name, resolve_inheritance=False)
                        
                        # Get enabled PII types
                        enabled_pii_types = []
                        for pii_type, enabled in profile.visual_rules.items():
                            if enabled:
                                enabled_pii_types.append(pii_type)
                        for pii_type, enabled in profile.text_rules.items():
                            if enabled:
                                enabled_pii_types.append(pii_type)
                        
                        print(f"  {name}")
                        
                        if args.verbose:
                            print(f"    Path: {path if path else 'unknown'}")
                            print(f"    Description: {profile.description}")
                            print(f"    PII Types: {', '.join(enabled_pii_types)}")
                            print(f"    Redaction Style: {profile.redaction_style.value}")
                            print()
                        else:
                            print(f"    {profile.description}")
                    
                    except Exception as e:
                        print(f"  {name} (ERROR: {e})")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to list profiles: {e}")
            return 1
    
    def _show_profile(self, args: argparse.Namespace) -> int:
        """Show detailed profile information."""
        
        try:
            profile_manager = ProfileManager()
            profile = profile_manager.load_profile(args.name)
            
            # Get enabled PII types
            enabled_pii_types = []
            for pii_type, enabled in profile.visual_rules.items():
                if enabled:
                    enabled_pii_types.append(pii_type)
            for pii_type, enabled in profile.text_rules.items():
                if enabled:
                    enabled_pii_types.append(pii_type)
            
            if args.format == 'json':
                self.print_json({
                    'name': profile.name,
                    'description': profile.description,
                    'pii_types': enabled_pii_types,
                    'redaction_style': profile.redaction_style.value,
                    'confidence_threshold': profile.confidence_threshold,
                    'visual_rules': profile.visual_rules,
                    'text_rules': profile.text_rules,
                    'multilingual_support': profile.multilingual_support
                })
            
            else:
                print(f"Profile: {profile.name}")
                print(f"Description: {profile.description}")
                print(f"PII Types: {', '.join(enabled_pii_types)}")
                print(f"Redaction Style: {profile.redaction_style.value}")
                print(f"Confidence Threshold: {profile.confidence_threshold}")
                print(f"Multilingual Support: {', '.join(profile.multilingual_support) if profile.multilingual_support else 'None'}")
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to show profile '{args.name}': {e}")
            return 1
    
    def _create_profile(self, args: argparse.Namespace) -> int:
        """Create a new profile."""
        
        try:
            # Start with base profile if specified
            if args.based_on:
                profile_manager = ProfileManager()
                base_profile = profile_manager.load_profile(args.based_on)
                profile = RedactionProfile(
                    name=args.name,
                    description=args.description or f"Profile based on {args.based_on}",
                    visual_rules=base_profile.visual_rules.copy(),
                    text_rules=base_profile.text_rules.copy(),
                    redaction_style=base_profile.redaction_style,
                    confidence_threshold=base_profile.confidence_threshold,
                    multilingual_support=base_profile.multilingual_support.copy()
                )
            else:
                # Create new profile with defaults
                visual_rules = {}
                text_rules = {}
                
                # Set default PII types if specified
                if args.pii_types:
                    for pii_type_str in args.pii_types:
                        pii_type = PIIType(pii_type_str.upper())
                        if pii_type in PIIType.visual_types():
                            visual_rules[pii_type.value] = True
                        else:
                            text_rules[pii_type.value] = True
                else:
                    # Default PII types
                    text_rules = {
                        PIIType.NAME.value: True,
                        PIIType.EMAIL.value: True,
                        PIIType.PHONE.value: True
                    }
                
                profile = RedactionProfile(
                    name=args.name,
                    description=args.description or f"Custom profile: {args.name}",
                    visual_rules=visual_rules,
                    text_rules=text_rules,
                    redaction_style=RedactionStyle.SOLID_BLACK,
                    confidence_threshold=0.8,
                    multilingual_support=[]
                )
            
            # Apply command line overrides for redaction style
            if args.redaction_style:
                profile.redaction_style = RedactionStyle(args.redaction_style.upper())
            
            # Determine output path
            output_path = args.output
            if not output_path:
                profiles_dir = Path('profiles')
                profiles_dir.mkdir(exist_ok=True)
                output_path = profiles_dir / f"{args.name}.yaml"
            
            # Check if profile already exists
            if output_path.exists():
                if not self.confirm_action(f"Profile file {output_path} exists. Overwrite?"):
                    self.logger.info("Profile creation cancelled")
                    return 0
            
            # Save profile
            if output_path.suffix.lower() in ['.yaml', '.yml']:
                profile.save_yaml(output_path)
            elif output_path.suffix.lower() == '.json':
                profile.save_json(output_path)
            else:
                # Default to YAML
                output_path = output_path.with_suffix('.yaml')
                profile.save_yaml(output_path)
            
            print(self.format_success(
                f"Profile '{args.name}' created",
                {'path': output_path}
            ))
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to create profile: {e}")
            return 1
    
    def _edit_profile(self, args: argparse.Namespace) -> int:
        """Edit an existing profile."""
        
        try:
            # Load existing profile
            profile_manager = ProfileManager()
            profile = profile_manager.load_profile(args.name)
            
            # Apply modifications
            modified = False
            
            if args.description:
                profile.description = args.description
                modified = True
            
            if args.add_pii_types:
                for pii_type_str in args.add_pii_types:
                    try:
                        pii_type = PIIType(pii_type_str.upper())
                        if pii_type in PIIType.visual_types():
                            if pii_type.value not in profile.visual_rules or not profile.visual_rules[pii_type.value]:
                                profile.visual_rules[pii_type.value] = True
                                modified = True
                        else:
                            if pii_type.value not in profile.text_rules or not profile.text_rules[pii_type.value]:
                                profile.text_rules[pii_type.value] = True
                                modified = True
                    except ValueError:
                        self.logger.warning(f"Invalid PII type: {pii_type_str}")
            
            if args.remove_pii_types:
                for pii_type_str in args.remove_pii_types:
                    try:
                        pii_type = PIIType(pii_type_str.upper())
                        if pii_type in PIIType.visual_types():
                            if pii_type.value in profile.visual_rules and profile.visual_rules[pii_type.value]:
                                profile.visual_rules[pii_type.value] = False
                                modified = True
                        else:
                            if pii_type.value in profile.text_rules and profile.text_rules[pii_type.value]:
                                profile.text_rules[pii_type.value] = False
                                modified = True
                    except ValueError:
                        self.logger.warning(f"Invalid PII type: {pii_type_str}")
            
            if args.redaction_style:
                profile.redaction_style = RedactionStyle(args.redaction_style.upper())
                modified = True
            
            if not modified:
                self.logger.info("No modifications specified")
                return 0
            
            # Save modified profile
            profile_manager = ProfileManager()
            output_path = profile_manager.save_profile(profile)
            
            print(self.format_success(
                f"Profile '{args.name}' updated",
                {'path': output_path}
            ))
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to edit profile '{args.name}': {e}")
            return 1
    
    def _validate_profile(self, args: argparse.Namespace) -> int:
        """Validate a profile."""
        
        try:
            # Load profile (by name or file path)
            if Path(args.profile).exists():
                profile_path = Path(args.profile)
                if profile_path.suffix.lower() in ['.yaml', '.yml']:
                    profile = RedactionProfile.from_yaml(profile_path)
                elif profile_path.suffix.lower() == '.json':
                    profile = RedactionProfile.from_json(profile_path)
                else:
                    raise ValueError(f"Unsupported profile file format: {profile_path.suffix}")
            else:
                profile_manager = ProfileManager()
                profile = profile_manager.load_profile(args.profile)
            
            # Validate profile
            profile_manager = ProfileManager()
            errors = profile_manager.validate_profile(profile)
            is_valid = len(errors) == 0
            
            if args.format == 'json':
                self.print_json({
                    'profile': args.profile,
                    'valid': is_valid,
                    'errors': errors
                })
            
            else:
                status = "✓ VALID" if is_valid else "✗ INVALID"
                print(f"Profile Validation: {status}")
                print(f"Profile: {profile.name}")
                
                if errors:
                    print(f"\nValidation Errors:")
                    for error in errors:
                        print(f"  • {error}")
                else:
                    print("No validation errors found.")
            
            return 0 if is_valid else 1
            
        except Exception as e:
            if args.format == 'json':
                self.print_json({
                    'profile': args.profile,
                    'valid': False,
                    'error': str(e)
                })
            else:
                print(self.format_error(f"Profile validation failed: {e}"))
            
            return 1
    
    def _delete_profile(self, args: argparse.Namespace) -> int:
        """Delete a profile."""
        
        try:
            # Find profile file
            profile_manager = ProfileManager()
            profile_names = profile_manager.list_profiles()
            
            if args.name not in profile_names:
                self.logger.error(f"Profile '{args.name}' not found")
                return 1
            
            profile_path = self._find_profile_path(args.name)
            
            # Confirm deletion
            if not args.force:
                if not self.confirm_action(f"Delete profile '{args.name}' ({profile_path})?"):
                    self.logger.info("Profile deletion cancelled")
                    return 0
            
            # Delete profile file
            profile_path.unlink()
            
            print(self.format_success(f"Profile '{args.name}' deleted"))
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete profile '{args.name}': {e}")
            return 1
    
    def _find_profile_path(self, name: str) -> Optional[Path]:
        """Find the file path for a profile by name."""
        
        # Search in profiles directory
        profiles_dir = Path('profiles')
        if profiles_dir.exists():
            for extension in ['.yaml', '.yml', '.json']:
                profile_path = profiles_dir / f"{name}{extension}"
                if profile_path.exists():
                    return profile_path
        
        return None