"""
Unit tests for document analyzer functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import tempfile
import os

from src.gopnik.core.analyzer import DocumentAnalyzer
from src.gopnik.models.processing import Document, DocumentFormat, PageInfo
from src.gopnik.models.errors import DocumentProcessingError


class TestDocumentAnalyzer:
    """Test cases for DocumentAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = DocumentAnalyzer()
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temp files
        for file in self.temp_dir.glob('*'):
            file.unlink()
        self.temp_dir.rmdir()
    
    def test_init(self):
        """Test analyzer initialization."""
        assert self.analyzer.supported_formats == ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        assert self.analyzer.max_file_size == 100 * 1024 * 1024
        assert self.analyzer.default_dpi == 150
    
    def test_is_supported_format(self):
        """Test format support checking."""
        # Supported formats
        assert self.analyzer.is_supported_format(Path('test.pdf'))
        assert self.analyzer.is_supported_format(Path('test.PNG'))
        assert self.analyzer.is_supported_format(Path('test.jpg'))
        assert self.analyzer.is_supported_format(Path('test.JPEG'))
        assert self.analyzer.is_supported_format(Path('test.tiff'))
        assert self.analyzer.is_supported_format(Path('test.bmp'))
        
        # Unsupported formats
        assert not self.analyzer.is_supported_format(Path('test.txt'))
        assert not self.analyzer.is_supported_format(Path('test.docx'))
        assert not self.analyzer.is_supported_format(Path('test.gif'))
    
    def test_validate_file_nonexistent(self):
        """Test validation of non-existent file."""
        nonexistent_path = self.temp_dir / 'nonexistent.pdf'
        
        with pytest.raises(DocumentProcessingError, match="File does not exist"):
            self.analyzer._validate_file(nonexistent_path)
    
    def test_validate_file_directory(self):
        """Test validation of directory path."""
        with pytest.raises(DocumentProcessingError, match="Path is not a file"):
            self.analyzer._validate_file(self.temp_dir)
    
    def test_validate_file_empty(self):
        """Test validation of empty file."""
        empty_file = self.temp_dir / 'empty.pdf'
        empty_file.touch()
        
        with pytest.raises(DocumentProcessingError, match="File is empty"):
            self.analyzer._validate_file(empty_file)
    
    def test_validate_file_unsupported_format(self):
        """Test validation of unsupported format."""
        unsupported_file = self.temp_dir / 'test.txt'
        unsupported_file.write_text('test content')
        
        with pytest.raises(DocumentProcessingError, match="Unsupported format"):
            self.analyzer._validate_file(unsupported_file)
    
    def test_validate_file_too_large(self):
        """Test validation of oversized file."""
        large_file = self.temp_dir / 'large.pdf'
        
        # Mock file size to be larger than limit
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value.st_size = self.analyzer.max_file_size + 1
            mock_stat.return_value.st_ctime = 1234567890
            mock_stat.return_value.st_mtime = 1234567890
            
            with patch.object(Path, 'exists', return_value=True):
                with patch.object(Path, 'is_file', return_value=True):
                    with pytest.raises(DocumentProcessingError, match="File too large"):
                        self.analyzer._validate_file(large_file)
    
    @patch('src.gopnik.core.analyzer.Image.open')
    def test_extract_image_pages_success(self, mock_image_open):
        """Test successful image page extraction."""
        # Create test image file
        test_image = self.temp_dir / 'test.png'
        test_image.write_bytes(b'fake image data')
        
        # Mock PIL Image
        mock_img = Mock()
        mock_img.mode = 'RGB'
        mock_img.size = (800, 600)
        mock_img.info = {'dpi': (150, 150)}
        mock_img.format = 'PNG'
        mock_img.getbands.return_value = ['R', 'G', 'B']
        
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        pages = self.analyzer._extract_image_pages(test_image)
        
        assert len(pages) == 1
        page = pages[0]
        assert isinstance(page, PageInfo)
        assert page.page_number == 0
        assert page.width == 800
        assert page.height == 600
        assert page.dpi == 150.0
        assert page.rotation == 0
        assert page.text_content is None
        assert page.metadata['image_mode'] == 'RGB'
        assert page.metadata['image_format'] == 'PNG'
    
    @patch('src.gopnik.core.analyzer.Image.open')
    def test_extract_image_pages_rgba_conversion(self, mock_image_open):
        """Test image page extraction with RGBA conversion."""
        test_image = self.temp_dir / 'test.png'
        test_image.write_bytes(b'fake image data')
        
        # Mock PIL Image with RGBA mode
        mock_img = Mock()
        mock_img.mode = 'RGBA'
        mock_img.size = (400, 300)
        mock_img.info = {'dpi': (72, 72)}
        mock_img.format = 'PNG'
        mock_img.convert.return_value = mock_img  # Return self for convert
        mock_img.getbands.return_value = ['R', 'G', 'B', 'A']
        
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        pages = self.analyzer._extract_image_pages(test_image)
        
        assert len(pages) == 1
        page = pages[0]
        assert page.metadata['has_transparency'] == True
    
    @patch('src.gopnik.core.analyzer.Image.open')
    def test_extract_image_pages_error(self, mock_image_open):
        """Test image page extraction error handling."""
        test_image = self.temp_dir / 'test.png'
        test_image.write_bytes(b'fake image data')
        
        mock_image_open.side_effect = Exception("Invalid image")
        
        with pytest.raises(DocumentProcessingError, match="Failed to extract image page"):
            self.analyzer._extract_image_pages(test_image)
    
    @patch('src.gopnik.core.analyzer.fitz.open')
    def test_extract_pdf_pages_success(self, mock_fitz_open):
        """Test successful PDF page extraction."""
        test_pdf = self.temp_dir / 'test.pdf'
        test_pdf.write_bytes(b'fake pdf data')
        
        # Mock PyMuPDF document and page
        mock_page = Mock()
        mock_page.rect.width = 612
        mock_page.rect.height = 792
        mock_page.rotation = 0
        mock_page.get_text.return_value = "Sample text content"
        
        mock_pix = Mock()
        mock_pix.tobytes.return_value = b'fake image data'
        mock_page.get_pixmap.return_value = mock_pix
        
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=2)
        mock_doc.load_page.return_value = mock_page
        mock_doc.close = Mock()
        
        mock_fitz_open.return_value = mock_doc
        
        pages = self.analyzer._extract_pdf_pages(test_pdf)
        
        assert len(pages) == 2
        page = pages[0]
        assert isinstance(page, PageInfo)
        assert page.page_number == 0
        assert page.width == 612
        assert page.height == 792
        assert page.dpi == 150
        assert page.text_content == "Sample text content"
        assert page.metadata['has_text'] == True
        
        mock_doc.close.assert_called_once()
    
    @patch('src.gopnik.core.analyzer.fitz.open')
    def test_extract_pdf_pages_error(self, mock_fitz_open):
        """Test PDF page extraction error handling."""
        test_pdf = self.temp_dir / 'test.pdf'
        test_pdf.write_bytes(b'fake pdf data')
        
        mock_fitz_open.side_effect = Exception("Invalid PDF")
        
        with pytest.raises(DocumentProcessingError, match="Failed to extract PDF pages"):
            self.analyzer._extract_pdf_pages(test_pdf)
    
    @patch('src.gopnik.core.analyzer.Image.open')
    def test_analyze_document_image_success(self, mock_image_open):
        """Test successful image document analysis."""
        test_image = self.temp_dir / 'test.jpg'
        test_image.write_bytes(b'fake image data')
        
        # Mock PIL Image
        mock_img = Mock()
        mock_img.mode = 'RGB'
        mock_img.size = (1024, 768)
        mock_img.info = {'dpi': (300, 300)}
        mock_img.format = 'JPEG'
        mock_img.getbands.return_value = ['R', 'G', 'B']
        
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        document = self.analyzer.analyze_document(test_image)
        
        assert isinstance(document, Document)
        assert document.format == DocumentFormat.JPG  # .jpg extension maps to JPG format
        assert document.page_count == 1
        assert document.path == test_image
        assert len(document.pages) == 1
        
        page = document.pages[0]
        assert page.width == 1024
        assert page.height == 768
        assert page.dpi == 300.0
    
    @patch('src.gopnik.core.analyzer.fitz.open')
    def test_analyze_document_pdf_success(self, mock_fitz_open):
        """Test successful PDF document analysis."""
        test_pdf = self.temp_dir / 'test.pdf'
        test_pdf.write_bytes(b'fake pdf data')
        
        # Mock PyMuPDF
        mock_page = Mock()
        mock_page.rect.width = 612
        mock_page.rect.height = 792
        mock_page.rotation = 0
        mock_page.get_text.return_value = "Test content"
        
        mock_pix = Mock()
        mock_pix.tobytes.return_value = b'image data'
        mock_page.get_pixmap.return_value = mock_pix
        
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.load_page.return_value = mock_page
        mock_doc.close = Mock()
        
        mock_fitz_open.return_value = mock_doc
        
        document = self.analyzer.analyze_document(test_pdf)
        
        assert isinstance(document, Document)
        assert document.format == DocumentFormat.PDF
        assert document.page_count == 1
        assert len(document.pages) == 1
        
        page = document.pages[0]
        assert page.text_content == "Test content"
    
    def test_analyze_document_unsupported_format(self):
        """Test analysis of unsupported format."""
        test_file = self.temp_dir / 'test.txt'
        test_file.write_text('test content')
        
        with pytest.raises(DocumentProcessingError, match="Document analysis failed"):
            self.analyzer.analyze_document(test_file)
    
    @patch('src.gopnik.core.analyzer.Image.open')
    def test_get_document_metadata_image(self, mock_image_open):
        """Test metadata extraction from image."""
        test_image = self.temp_dir / 'test.png'
        test_image.write_bytes(b'fake image data')
        
        mock_img = Mock()
        mock_img.width = 800
        mock_img.height = 600
        mock_img.mode = 'RGB'
        mock_img.format = 'PNG'
        mock_img.info = {'dpi': (150, 150)}
        
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        metadata = self.analyzer.get_document_metadata(test_image)
        
        assert metadata['filename'] == 'test.png'
        assert metadata['format'] == 'png'  # This comes from DocumentFormat.from_path()
        assert metadata['page_count'] == 1
        assert metadata['width'] == 800
        assert metadata['height'] == 600
        assert metadata['mode'] == 'RGB'
    
    @patch('src.gopnik.core.analyzer.fitz.open')
    def test_get_document_metadata_pdf(self, mock_fitz_open):
        """Test metadata extraction from PDF."""
        test_pdf = self.temp_dir / 'test.pdf'
        test_pdf.write_bytes(b'fake pdf data')
        
        mock_doc = Mock()
        mock_doc.__len__ = Mock(return_value=3)
        mock_doc.metadata = {
            'title': 'Test Document',
            'author': 'Test Author',
            'creator': 'Test Creator'
        }
        mock_doc.needs_pass = False
        mock_doc.pdf_version.return_value = '1.4'
        mock_doc.close = Mock()
        
        mock_fitz_open.return_value = mock_doc
        
        metadata = self.analyzer.get_document_metadata(test_pdf)
        
        assert metadata['filename'] == 'test.pdf'
        assert metadata['format'] == 'pdf'
        assert metadata['page_count'] == 3
        assert metadata['title'] == 'Test Document'
        assert metadata['author'] == 'Test Author'
        assert metadata['encrypted'] == False
        assert metadata['pdf_version'] == '1.4'
    
    def test_check_consistent_page_sizes(self):
        """Test page size consistency checking."""
        # Consistent pages
        pages = [
            PageInfo(0, 800, 600, 72.0),
            PageInfo(1, 805, 595, 72.0),  # Within tolerance
            PageInfo(2, 798, 602, 72.0)   # Within tolerance
        ]
        assert self.analyzer._check_consistent_page_sizes(pages) == True
        
        # Inconsistent pages
        pages = [
            PageInfo(0, 800, 600, 72.0),
            PageInfo(1, 1200, 900, 72.0),  # Different size
        ]
        assert self.analyzer._check_consistent_page_sizes(pages) == False
        
        # Empty list
        assert self.analyzer._check_consistent_page_sizes([]) == True
    
    def test_determine_document_orientation(self):
        """Test document orientation determination."""
        # Portrait pages
        portrait_pages = [
            PageInfo(0, 600, 800, 72.0),
            PageInfo(1, 600, 800, 72.0)
        ]
        assert self.analyzer._determine_document_orientation(portrait_pages) == 'portrait'
        
        # Landscape pages
        landscape_pages = [
            PageInfo(0, 800, 600, 72.0),
            PageInfo(1, 800, 600, 72.0)
        ]
        assert self.analyzer._determine_document_orientation(landscape_pages) == 'landscape'
        
        # Mixed pages
        mixed_pages = [
            PageInfo(0, 600, 800, 72.0),  # Portrait
            PageInfo(1, 800, 600, 72.0)   # Landscape
        ]
        assert self.analyzer._determine_document_orientation(mixed_pages) == 'mixed'
        
        # Empty list
        assert self.analyzer._determine_document_orientation([]) == 'unknown'
    
    @patch('src.gopnik.core.analyzer.Image.open')
    def test_extract_pages_integration(self, mock_image_open):
        """Test extract_pages method integration."""
        test_image = self.temp_dir / 'test.png'
        test_image.write_bytes(b'fake image data')
        
        mock_img = Mock()
        mock_img.mode = 'RGB'
        mock_img.size = (400, 300)
        mock_img.info = {'dpi': (72, 72)}
        mock_img.format = 'PNG'
        mock_img.getbands.return_value = ['R', 'G', 'B']
        
        mock_image_open.return_value.__enter__.return_value = mock_img
        
        pages_data = self.analyzer.extract_pages(test_image)
        
        assert len(pages_data) == 1
        page_data = pages_data[0]
        assert page_data['page_number'] == 0
        assert page_data['width'] == 400
        assert page_data['height'] == 300
        assert page_data['area'] == 120000


if __name__ == '__main__':
    pytest.main([__file__])