"""
Integration tests for CLI processing workflows.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import argparse

from src.gopnik.interfaces.cli.commands.process_command import ProcessCommand
from src.gopnik.interfaces.cli.commands.batch_command import BatchCommand
from src.gopnik.config import GopnikConfig
from src.gopnik.models.profiles import RedactionProfile, RedactionStyle
from src.gopnik.models.processing import ProcessingResult, ProcessingStatus
from src.gopnik.models.pii import PIIDetectionCollection


class TestProcessCommandIntegration:
    """Integration tests for process command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=GopnikConfig)
        self.command = ProcessCommand(self.config)
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test files
        self.test_input = self.temp_dir / "test_document.pdf"
        self.test_input.write_text("Test document content")
        
        self.test_profile = self.temp_dir / "test_profile.yaml"
        self.test_profile.write_text("""
name: test_profile
description: Test profile
visual_rules:
  face: true
text_rules:
  name: true
  email: true
redaction_style: solid_black
confidence_threshold: 0.8
""")
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    @patch('src.gopnik.interfaces.cli.commands.process_command.DocumentProcessor')
    @patch('src.gopnik.interfaces.cli.commands.process_command.ProfileManager')
    def test_process_command_success(self, mock_profile_manager, mock_processor_class):
        """Test successful document processing."""
        # Mock profile loading
        mock_profile = Mock(spec=RedactionProfile)
        mock_profile.name = "test_profile"
        mock_profile_manager_instance = Mock()
        mock_profile_manager_instance.load_profile.return_value = mock_profile
        mock_profile_manager.return_value = mock_profile_manager_instance
        
        # Mock processor
        mock_processor = Mock()
        mock_result = Mock(spec=ProcessingResult)
        mock_result.success = True
        mock_result.output_path = self.temp_dir / "output.pdf"
        mock_result.detections = PIIDetectionCollection()
        mock_result.metrics = Mock()
        mock_result.metrics.total_time = 2.5
        mock_processor.process_document.return_value = mock_result
        mock_processor_class.return_value = mock_processor
        
        # Create arguments
        args = argparse.Namespace(
            input=self.test_input,
            output=None,
            profile='test_profile',
            profile_file=None,
            dry_run=False,
            force=False,
            no_audit=False,
            format='text'
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify success
        assert result == 0
        mock_processor.process_document.assert_called_once_with(self.test_input, mock_profile)
    
    @patch('src.gopnik.interfaces.cli.commands.process_command.DocumentProcessor')
    @patch('src.gopnik.interfaces.cli.commands.process_command.ProfileManager')
    def test_process_command_with_custom_profile(self, mock_profile_manager, mock_processor_class):
        """Test processing with custom profile file."""
        # Mock profile loading from file
        mock_profile = Mock(spec=RedactionProfile)
        mock_profile.name = "custom_profile"
        
        with patch('src.gopnik.models.profiles.RedactionProfile.from_yaml', return_value=mock_profile):
            # Mock processor
            mock_processor = Mock()
            mock_result = Mock(spec=ProcessingResult)
            mock_result.success = True
            mock_result.output_path = self.temp_dir / "output.pdf"
            mock_result.detections = PIIDetectionCollection()
            mock_result.metrics = Mock()
            mock_result.metrics.total_time = 1.8
            mock_processor.process_document.return_value = mock_result
            mock_processor_class.return_value = mock_processor
            
            # Create arguments
            args = argparse.Namespace(
                input=self.test_input,
                output=None,
                profile='default',
                profile_file=self.test_profile,
                dry_run=False,
                force=False,
                no_audit=False,
                format='json'
            )
            
            # Execute command
            result = self.command.execute(args)
            
            # Verify success
            assert result == 0
            mock_processor.process_document.assert_called_once_with(self.test_input, mock_profile)
    
    @patch('src.gopnik.interfaces.cli.commands.process_command.ProfileManager')
    def test_process_command_dry_run(self, mock_profile_manager):
        """Test dry run mode."""
        # Mock profile loading
        mock_profile = Mock(spec=RedactionProfile)
        mock_profile.name = "test_profile"
        mock_profile.description = "Test profile"
        mock_profile.visual_rules = {"face": True}
        mock_profile.text_rules = {"name": True, "email": True}
        mock_profile.redaction_style = RedactionStyle.SOLID_BLACK
        mock_profile_manager_instance = Mock()
        mock_profile_manager_instance.load_profile.return_value = mock_profile
        mock_profile_manager.return_value = mock_profile_manager_instance
        
        # Create arguments
        args = argparse.Namespace(
            input=self.test_input,
            output=None,
            profile='test_profile',
            profile_file=None,
            dry_run=True,
            force=False,
            no_audit=False,
            format='text'
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify success (dry run should not process)
        assert result == 0
    
    def test_process_command_invalid_input(self):
        """Test processing with invalid input file."""
        args = argparse.Namespace(
            input=Path("nonexistent.pdf"),
            output=None,
            profile='default',
            profile_file=None,
            dry_run=False,
            force=False,
            no_audit=False,
            format='text'
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify failure
        assert result == 1


class TestBatchCommandIntegration:
    """Integration tests for batch command."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = Mock(spec=GopnikConfig)
        self.command = BatchCommand(self.config)
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test input directory with files
        self.input_dir = self.temp_dir / "input"
        self.input_dir.mkdir()
        
        # Create test documents
        (self.input_dir / "doc1.pdf").write_text("Document 1 content")
        (self.input_dir / "doc2.pdf").write_text("Document 2 content")
        (self.input_dir / "image.jpg").write_text("Image content")
        (self.input_dir / "readme.txt").write_text("Text file")  # Should be ignored
        
        # Create subdirectory
        subdir = self.input_dir / "subdir"
        subdir.mkdir()
        (subdir / "doc3.pdf").write_text("Document 3 content")
    
    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    @patch('src.gopnik.interfaces.cli.commands.batch_command.DocumentProcessor')
    @patch('src.gopnik.interfaces.cli.commands.batch_command.ProfileManager')
    def test_batch_command_success(self, mock_profile_manager, mock_processor_class):
        """Test successful batch processing."""
        # Mock profile loading
        mock_profile = Mock(spec=RedactionProfile)
        mock_profile.name = "test_profile"
        mock_profile_manager_instance = Mock()
        mock_profile_manager_instance.load_profile.return_value = mock_profile
        mock_profile_manager.return_value = mock_profile_manager_instance
        
        # Mock processor
        mock_processor = Mock()
        mock_result = Mock(spec=ProcessingResult)
        mock_result.success = True
        mock_result.output_path = Mock()
        mock_result.detections = PIIDetectionCollection()
        mock_result.metrics = Mock()
        mock_result.metrics.total_time = 1.5
        mock_processor.process_document.return_value = mock_result
        mock_processor_class.return_value = mock_processor
        
        # Create arguments
        args = argparse.Namespace(
            input_dir=self.input_dir,
            output=None,
            profile='test_profile',
            profile_file=None,
            recursive=False,
            pattern=None,
            dry_run=False,
            force=False,
            continue_on_error=True,
            max_files=None,
            format='text',
            progress=False
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify success
        assert result == 0
        # Should process PDF and JPG files (2 files)
        assert mock_processor.process_document.call_count == 2
    
    @patch('src.gopnik.interfaces.cli.commands.batch_command.DocumentProcessor')
    @patch('src.gopnik.interfaces.cli.commands.batch_command.ProfileManager')
    def test_batch_command_recursive(self, mock_profile_manager, mock_processor_class):
        """Test batch processing with recursive option."""
        # Mock profile loading
        mock_profile = Mock(spec=RedactionProfile)
        mock_profile.name = "test_profile"
        mock_profile_manager_instance = Mock()
        mock_profile_manager_instance.load_profile.return_value = mock_profile
        mock_profile_manager.return_value = mock_profile_manager_instance
        
        # Mock processor
        mock_processor = Mock()
        mock_result = Mock(spec=ProcessingResult)
        mock_result.success = True
        mock_result.output_path = Mock()
        mock_result.detections = PIIDetectionCollection()
        mock_result.metrics = Mock()
        mock_result.metrics.total_time = 1.5
        mock_processor.process_document.return_value = mock_result
        mock_processor_class.return_value = mock_processor
        
        # Create arguments
        args = argparse.Namespace(
            input_dir=self.input_dir,
            output=None,
            profile='test_profile',
            profile_file=None,
            recursive=True,
            pattern=None,
            dry_run=False,
            force=False,
            continue_on_error=True,
            max_files=None,
            format='text',
            progress=False
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify success
        assert result == 0
        # Should process PDF and JPG files including subdirectory (3 files)
        assert mock_processor.process_document.call_count == 3
    
    @patch('src.gopnik.interfaces.cli.commands.batch_command.ProfileManager')
    def test_batch_command_dry_run(self, mock_profile_manager):
        """Test batch processing dry run."""
        # Mock profile loading
        mock_profile = Mock(spec=RedactionProfile)
        mock_profile.name = "test_profile"
        mock_profile.description = "Test profile"
        mock_profile_manager_instance = Mock()
        mock_profile_manager_instance.load_profile.return_value = mock_profile
        mock_profile_manager.return_value = mock_profile_manager_instance
        
        # Create arguments
        args = argparse.Namespace(
            input_dir=self.input_dir,
            output=None,
            profile='test_profile',
            profile_file=None,
            recursive=False,
            pattern=None,
            dry_run=True,
            force=False,
            continue_on_error=True,
            max_files=None,
            format='text',
            progress=False
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify success (dry run should not process)
        assert result == 0
    
    @patch('src.gopnik.interfaces.cli.commands.batch_command.DocumentProcessor')
    @patch('src.gopnik.interfaces.cli.commands.batch_command.ProfileManager')
    def test_batch_command_with_pattern(self, mock_profile_manager, mock_processor_class):
        """Test batch processing with file pattern."""
        # Mock profile loading
        mock_profile = Mock(spec=RedactionProfile)
        mock_profile.name = "test_profile"
        mock_profile_manager_instance = Mock()
        mock_profile_manager_instance.load_profile.return_value = mock_profile
        mock_profile_manager.return_value = mock_profile_manager_instance
        
        # Mock processor
        mock_processor = Mock()
        mock_result = Mock(spec=ProcessingResult)
        mock_result.success = True
        mock_result.output_path = Mock()
        mock_result.detections = PIIDetectionCollection()
        mock_result.metrics = Mock()
        mock_result.metrics.total_time = 1.5
        mock_processor.process_document.return_value = mock_result
        mock_processor_class.return_value = mock_processor
        
        # Create arguments
        args = argparse.Namespace(
            input_dir=self.input_dir,
            output=None,
            profile='test_profile',
            profile_file=None,
            recursive=False,
            pattern='*.pdf',
            dry_run=False,
            force=False,
            continue_on_error=True,
            max_files=None,
            format='text',
            progress=False
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify success
        assert result == 0
        # Should only process PDF files (2 files)
        assert mock_processor.process_document.call_count == 2
    
    @patch('src.gopnik.interfaces.cli.commands.batch_command.DocumentProcessor')
    @patch('src.gopnik.interfaces.cli.commands.batch_command.ProfileManager')
    def test_batch_command_max_files(self, mock_profile_manager, mock_processor_class):
        """Test batch processing with max files limit."""
        # Mock profile loading
        mock_profile = Mock(spec=RedactionProfile)
        mock_profile.name = "test_profile"
        mock_profile_manager_instance = Mock()
        mock_profile_manager_instance.load_profile.return_value = mock_profile
        mock_profile_manager.return_value = mock_profile_manager_instance
        
        # Mock processor
        mock_processor = Mock()
        mock_result = Mock(spec=ProcessingResult)
        mock_result.success = True
        mock_result.output_path = Mock()
        mock_result.detections = PIIDetectionCollection()
        mock_result.metrics = Mock()
        mock_result.metrics.total_time = 1.5
        mock_processor.process_document.return_value = mock_result
        mock_processor_class.return_value = mock_processor
        
        # Create arguments
        args = argparse.Namespace(
            input_dir=self.input_dir,
            output=None,
            profile='test_profile',
            profile_file=None,
            recursive=False,
            pattern=None,
            dry_run=False,
            force=False,
            continue_on_error=True,
            max_files=1,
            format='text',
            progress=False
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify success
        assert result == 0
        # Should only process 1 file due to max_files limit
        assert mock_processor.process_document.call_count == 1
    
    def test_batch_command_invalid_input_dir(self):
        """Test batch processing with invalid input directory."""
        args = argparse.Namespace(
            input_dir=Path("nonexistent_dir"),
            output=None,
            profile='default',
            profile_file=None,
            recursive=False,
            pattern=None,
            dry_run=False,
            force=False,
            continue_on_error=True,
            max_files=None,
            format='text',
            progress=False
        )
        
        # Execute command
        result = self.command.execute(args)
        
        # Verify failure
        assert result == 1


class TestProgressIntegration:
    """Test progress bar integration."""
    
    def test_progress_bar_creation(self):
        """Test progress bar creation and updates."""
        from src.gopnik.interfaces.cli.progress import create_progress_bar
        
        progress = create_progress_bar(10, "Test progress", True)
        assert progress is not None
        assert progress.total == 10
        assert progress.description == "Test progress"
        
        # Test updates
        progress.update(1)
        assert progress.current == 1
        
        progress.update(5)
        assert progress.current == 6
        
        progress.finish()
        assert progress.current == progress.total
    
    def test_progress_bar_disabled(self):
        """Test progress bar when disabled."""
        from src.gopnik.interfaces.cli.progress import create_progress_bar
        
        progress = create_progress_bar(10, "Test progress", False)
        assert progress is None
    
    def test_spinner_creation(self):
        """Test spinner creation and updates."""
        from src.gopnik.interfaces.cli.progress import create_spinner
        
        spinner = create_spinner("Test spinner", True)
        assert spinner is not None
        assert spinner.description == "Test spinner"
        
        # Test start/stop
        spinner.start()
        assert spinner.active is True
        
        spinner.update("Updated description")
        assert spinner.description == "Updated description"
        
        spinner.stop()
        assert spinner.active is False
    
    def test_spinner_disabled(self):
        """Test spinner when disabled."""
        from src.gopnik.interfaces.cli.progress import create_spinner
        
        spinner = create_spinner("Test spinner", False)
        assert spinner is None