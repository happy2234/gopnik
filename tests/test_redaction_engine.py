"""
Unit tests for redaction engine functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import tempfile
import io

from src.gopnik.core.redaction import RedactionEngine
from src.gopnik.models.pii import PIIDetection, PIIType, BoundingBox
from src.gopnik.models.profiles import RedactionProfile, RedactionStyle
from src.gopnik.models.processing import DocumentFormat
from src.gopnik.models.errors import DocumentProcessingError


class TestRedactionEngine:
    """Test cases for RedactionEngine class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RedactionEngine()
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test detection
        self.test_detection = PIIDetection(
            type=PIIType.NAME,
            bounding_box=BoundingBox(100, 100, 200, 150),
            confidence=0.9,
            text_content="John Doe",
            page_number=0
        )
        
        # Create test profile
        self.test_profile = RedactionProfile(
            name="test_profile",
            description="Test profile",
            text_rules={PIIType.NAME.value: True},
            redaction_style=RedactionStyle.SOLID_BLACK,
            confidence_threshold=0.8
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp files
        for file in self.temp_dir.glob('*'):
            file.unlink()
        self.temp_dir.rmdir()
    
    def test_init(self):
        """Test redaction engine initialization."""
        assert self.engine.preserve_layout() == True
        assert self.engine.temp_dir.exists()
        assert len(self.engine.style_configs) == 4
        assert RedactionStyle.SOLID_BLACK in self.engine.style_configs
    
    def test_preserve_layout(self):
        """Test layout preservation flag."""
        assert self.engine.preserve_layout() == True
    
    def test_filter_detections_by_profile(self):
        """Test detection filtering based on profile."""
        # Create detections with different types and confidences
        detections = [
            PIIDetection(PIIType.NAME, BoundingBox(0, 0, 100, 50), 0.9),
            PIIDetection(PIIType.EMAIL, BoundingBox(0, 50, 100, 100), 0.7),  # Low confidence
            PIIDetection(PIIType.PHONE, BoundingBox(0, 100, 100, 150), 0.95)  # Not in profile
        ]
        
        # Profile only redacts names and emails with confidence > 0.8
        profile = RedactionProfile(
            name="test",
            description="Test profile",
            text_rules={
                PIIType.NAME.value: True,
                PIIType.EMAIL.value: True
            },
            confidence_threshold=0.8
        )
        
        filtered = self.engine._filter_detections_by_profile(detections, profile)
        
        # Should only include NAME detection (high confidence, in profile)
        assert len(filtered) == 1
        assert filtered[0].type == PIIType.NAME
    
    def test_group_detections_by_page(self):
        """Test grouping detections by page number."""
        detections = [
            PIIDetection(PIIType.NAME, BoundingBox(0, 0, 100, 50), 0.9, page_number=0),
            PIIDetection(PIIType.EMAIL, BoundingBox(0, 50, 100, 100), 0.9, page_number=1),
            PIIDetection(PIIType.PHONE, BoundingBox(0, 100, 100, 150), 0.9, page_number=0)
        ]
        
        grouped = self.engine._group_detections_by_page(detections)
        
        assert len(grouped) == 2
        assert len(grouped[0]) == 2  # Page 0 has 2 detections
        assert len(grouped[1]) == 1  # Page 1 has 1 detection
        assert grouped[0][0].type == PIIType.NAME
        assert grouped[1][0].type == PIIType.EMAIL
    
    def test_create_copy(self):
        """Test document copying functionality."""
        # Create test file
        test_file = self.temp_dir / 'test.txt'
        test_file.write_text('test content')
        
        copy_path = self.engine._create_copy(test_file)
        
        assert copy_path.exists()
        assert copy_path.name.startswith('redacted_')
        assert copy_path.read_text() == 'test content'
    
    def test_get_text_replacement(self):
        """Test text replacement generation."""
        profile = RedactionProfile(
            name="test",
            description="Test profile"
        )
        
        # Test default replacements
        assert self.engine._get_text_replacement(PIIType.NAME, "John", profile) == "[NAME REDACTED]"
        assert self.engine._get_text_replacement(PIIType.EMAIL, "test@example.com", profile) == "[EMAIL REDACTED]"
        assert self.engine._get_text_replacement(PIIType.FACE, "", profile) == "[REDACTED]"
        
        # Test custom replacement
        profile.custom_rules = {PIIType.NAME.value: {'replacement_text': '[CUSTOM]'}}
        assert self.engine._get_text_replacement(PIIType.NAME, "John", profile) == "[CUSTOM]"
    
    def test_apply_text_redaction(self):
        """Test text content redaction."""
        text_content = "Hello John Doe, your email is john@example.com"
        detection = PIIDetection(
            type=PIIType.NAME,
            bounding_box=BoundingBox(0, 0, 100, 50),
            confidence=0.9,
            text_content="John Doe"
        )
        
        profile = RedactionProfile(
            name="test",
            description="Test profile",
            text_rules={PIIType.NAME.value: True}
        )
        
        redacted_text = self.engine._apply_text_redaction(text_content, detection, profile)
        
        assert "John Doe" not in redacted_text
        assert "[NAME REDACTED]" in redacted_text
        assert "john@example.com" in redacted_text  # Email should remain
    
    def test_apply_text_redaction_no_text_content(self):
        """Test text redaction when detection has no text content."""
        text_content = "Hello world"
        detection = PIIDetection(
            type=PIIType.FACE,
            bounding_box=BoundingBox(0, 0, 100, 50),
            confidence=0.9,
            text_content=None  # No text content
        )
        
        redacted_text = self.engine._apply_text_redaction(text_content, detection, self.test_profile)
        
        # Should return original text unchanged
        assert redacted_text == text_content
    
    @patch('src.gopnik.core.redaction.Image.open')
    def test_apply_visual_redaction(self, mock_image_open):
        """Test visual redaction on image data."""
        # Mock PIL Image
        mock_img = Mock()
        mock_redacted_img = Mock()
        
        mock_image_open.return_value = mock_img
        
        # Mock the redaction method
        with patch.object(self.engine, '_apply_image_detection_redaction', return_value=mock_redacted_img):
            # Mock save method
            mock_buffer = io.BytesIO(b'redacted_image_data')
            with patch('io.BytesIO', return_value=mock_buffer):
                mock_redacted_img.save = Mock()
                
                result = self.engine._apply_visual_redaction(b'image_data', self.test_detection, self.test_profile)
                
                # Should return the mocked buffer content
                assert isinstance(result, bytes)
    
    @patch('src.gopnik.core.redaction.Image.open')
    def test_apply_image_detection_redaction_solid_black(self, mock_image_open):
        """Test solid black redaction on image."""
        # Create mock image and draw
        mock_img = Mock()
        mock_draw = Mock()
        
        mock_image_open.return_value = mock_img
        
        with patch('src.gopnik.core.redaction.ImageDraw.Draw', return_value=mock_draw):
            result = self.engine._apply_image_detection_redaction(mock_img, self.test_detection, self.test_profile)
            
            # Should call rectangle with black color
            mock_draw.rectangle.assert_called_once()
            call_args = mock_draw.rectangle.call_args
            assert call_args[1]['fill'] == (0, 0, 0)  # Black color
    
    @patch('src.gopnik.core.redaction.Image.open')
    def test_apply_image_redactions_success(self, mock_image_open):
        """Test successful image redaction."""
        # Create test image file
        test_image = self.temp_dir / 'test.png'
        test_image.write_bytes(b'fake image data')
        
        # Mock PIL Image
        mock_img = Mock()
        mock_img.mode = 'RGB'
        mock_img.copy.return_value = mock_img
        mock_img.save = Mock()
        
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        # Mock the detection redaction
        with patch.object(self.engine, '_apply_image_detection_redaction', return_value=mock_img):
            result_path = self.engine._apply_image_redactions(test_image, [self.test_detection], self.test_profile)
            
            assert result_path.name.startswith('redacted_')
            mock_img.save.assert_called_once()
    
    @patch('src.gopnik.core.redaction.fitz.open')
    def test_apply_pdf_redactions_success(self, mock_fitz_open):
        """Test successful PDF redaction."""
        # Create test PDF file
        test_pdf = self.temp_dir / 'test.pdf'
        test_pdf.write_bytes(b'fake pdf data')
        
        # Mock PyMuPDF
        mock_page = Mock()
        mock_page.add_redact_annot = Mock()
        mock_page.apply_redactions = Mock()
        
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.load_page.return_value = mock_page
        mock_doc.save = Mock()
        mock_doc.close = Mock()
        
        mock_fitz_open.return_value = mock_doc
        
        result_path = self.engine._apply_pdf_redactions(test_pdf, [self.test_detection], self.test_profile)
        
        assert result_path.name.startswith('redacted_')
        mock_page.add_redact_annot.assert_called_once()
        mock_page.apply_redactions.assert_called_once()
        mock_doc.save.assert_called_once()
        mock_doc.close.assert_called_once()
    
    def test_apply_redactions_no_detections(self):
        """Test redaction with no detections."""
        test_file = self.temp_dir / 'test.txt'
        test_file.write_text('test content')
        
        with patch.object(self.engine, '_create_copy') as mock_copy:
            mock_copy.return_value = test_file
            
            result = self.engine.apply_redactions(test_file, [], self.test_profile)
            
            mock_copy.assert_called_once_with(test_file)
            assert result == test_file
    
    def test_apply_redactions_nonexistent_file(self):
        """Test redaction with non-existent file."""
        nonexistent_file = self.temp_dir / 'nonexistent.pdf'
        
        with pytest.raises(DocumentProcessingError, match="Document not found"):
            self.engine.apply_redactions(nonexistent_file, [self.test_detection], self.test_profile)
    
    @patch('src.gopnik.core.redaction.DocumentFormat.from_path')
    def test_apply_redactions_pdf_format(self, mock_format):
        """Test redaction routing for PDF format."""
        test_file = self.temp_dir / 'test.pdf'
        test_file.write_bytes(b'fake pdf')
        
        mock_format.return_value = DocumentFormat.PDF
        
        with patch.object(self.engine, '_apply_pdf_redactions') as mock_pdf_redact:
            mock_pdf_redact.return_value = test_file
            
            result = self.engine.apply_redactions(test_file, [self.test_detection], self.test_profile)
            
            mock_pdf_redact.assert_called_once()
    
    @patch('src.gopnik.core.redaction.DocumentFormat.from_path')
    def test_apply_redactions_image_format(self, mock_format):
        """Test redaction routing for image format."""
        test_file = self.temp_dir / 'test.png'
        test_file.write_bytes(b'fake image')
        
        mock_format.return_value = DocumentFormat.PNG
        
        with patch.object(self.engine, '_apply_image_redactions') as mock_image_redact:
            mock_image_redact.return_value = test_file
            
            result = self.engine.apply_redactions(test_file, [self.test_detection], self.test_profile)
            
            mock_image_redact.assert_called_once()
    
    def test_get_redaction_statistics(self):
        """Test redaction statistics generation."""
        detections = [
            PIIDetection(PIIType.NAME, BoundingBox(0, 0, 100, 50), 0.9, page_number=0),
            PIIDetection(PIIType.EMAIL, BoundingBox(0, 50, 100, 100), 0.7, page_number=0),  # Low confidence
            PIIDetection(PIIType.NAME, BoundingBox(0, 100, 100, 150), 0.95, page_number=1)
        ]
        
        profile = RedactionProfile(
            name="test",
            description="Test profile",
            text_rules={PIIType.NAME.value: True},
            confidence_threshold=0.8,
            redaction_style=RedactionStyle.SOLID_BLACK
        )
        
        stats = self.engine.get_redaction_statistics(detections, profile)
        
        assert stats['total_detections'] == 3
        assert stats['redacted_detections'] == 2  # Only NAME detections with high confidence
        assert stats['skipped_detections'] == 1
        assert stats['redaction_by_type']['name'] == 2
        assert stats['redaction_by_page'][0] == 1
        assert stats['redaction_by_page'][1] == 1
        assert stats['redaction_style'] == 'solid_black'
    
    def test_apply_pixelation(self):
        """Test pixelation effect application."""
        # Create a test image
        img = Image.new('RGB', (200, 200), color='red')
        bbox = BoundingBox(50, 50, 150, 150)
        
        result = self.engine._apply_pixelation(img, bbox)
        
        # Should return an image (basic test)
        assert isinstance(result, Image.Image)
        assert result.size == (200, 200)
    
    def test_apply_blur(self):
        """Test blur effect application."""
        # Create a test image
        img = Image.new('RGB', (200, 200), color='blue')
        bbox = BoundingBox(50, 50, 150, 150)
        
        result = self.engine._apply_blur(img, bbox)
        
        # Should return an image (basic test)
        assert isinstance(result, Image.Image)
        assert result.size == (200, 200)
    
    def test_style_configs(self):
        """Test redaction style configurations."""
        configs = self.engine.style_configs
        
        # Check all required styles are present
        assert RedactionStyle.SOLID_BLACK in configs
        assert RedactionStyle.SOLID_WHITE in configs
        assert RedactionStyle.PIXELATED in configs
        assert RedactionStyle.BLURRED in configs
        
        # Check solid black config
        black_config = configs[RedactionStyle.SOLID_BLACK]
        assert black_config['color'] == (0, 0, 0)
        assert black_config['pattern'] is None
        
        # Check pixelated config
        pixel_config = configs[RedactionStyle.PIXELATED]
        assert pixel_config['pattern'] == 'pixelate'
        assert pixel_config['color'] is None


if __name__ == '__main__':
    pytest.main([__file__])