"""
Document analyzer for parsing and structure analysis.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import mimetypes
from PIL import Image
import fitz  # PyMuPDF
import numpy as np

from ..models.processing import Document, DocumentFormat, PageInfo
from ..models.errors import DocumentProcessingError


class DocumentAnalyzer:
    """
    Handles document parsing and structure analysis.
    
    Responsible for extracting content and layout information from various
    document formats while preserving structural information.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']
        self.max_file_size = 100 * 1024 * 1024  # 100MB limit
        self.default_dpi = 150  # DPI for PDF to image conversion
    
    def analyze_document(self, document_path: Path) -> Document:
        """
        Analyze document structure and extract content.
        
        Args:
            document_path: Path to document file
            
        Returns:
            Document object with parsed content and structure
            
        Raises:
            DocumentProcessingError: If document cannot be analyzed
        """
        try:
            self.logger.info(f"Analyzing document: {document_path}")
            
            # Validate file
            self._validate_file(document_path)
            
            # Determine format
            doc_format = DocumentFormat.from_path(document_path)
            if doc_format == DocumentFormat.UNKNOWN:
                raise DocumentProcessingError(f"Unsupported document format: {document_path.suffix}")
            
            # Create document object
            document = Document(path=document_path, format=doc_format)
            
            # Extract pages based on format
            if doc_format == DocumentFormat.PDF:
                pages = self._extract_pdf_pages(document_path)
            else:
                pages = self._extract_image_pages(document_path)
            
            # Add pages to document
            for page in pages:
                document.add_page(page)
            
            # Extract document structure
            document.structure = self._analyze_document_structure(document)
            
            self.logger.info(f"Successfully analyzed document with {document.page_count} pages")
            return document
            
        except Exception as e:
            self.logger.error(f"Failed to analyze document {document_path}: {str(e)}")
            raise DocumentProcessingError(f"Document analysis failed: {str(e)}") from e
    
    def extract_pages(self, document_path: Path) -> List[Dict[str, Any]]:
        """
        Extract individual pages from multi-page documents.
        
        Args:
            document_path: Path to document file
            
        Returns:
            List of page data dictionaries
        """
        try:
            document = self.analyze_document(document_path)
            return [page.to_dict() for page in document.pages]
        except Exception as e:
            self.logger.error(f"Failed to extract pages from {document_path}: {str(e)}")
            raise DocumentProcessingError(f"Page extraction failed: {str(e)}") from e
    
    def get_document_metadata(self, document_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from document.
        
        Args:
            document_path: Path to document file
            
        Returns:
            Dictionary containing document metadata
        """
        try:
            self._validate_file(document_path)
            
            # Basic file metadata
            stat = document_path.stat()
            mime_type, _ = mimetypes.guess_type(str(document_path))
            
            metadata = {
                'filename': document_path.name,
                'file_size': stat.st_size,
                'mime_type': mime_type,
                'format': DocumentFormat.from_path(document_path).value,
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime
            }
            
            # Format-specific metadata
            doc_format = DocumentFormat.from_path(document_path)
            if doc_format == DocumentFormat.PDF:
                metadata.update(self._extract_pdf_metadata(document_path))
            else:
                metadata.update(self._extract_image_metadata(document_path))
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata from {document_path}: {str(e)}")
            raise DocumentProcessingError(f"Metadata extraction failed: {str(e)}") from e
    
    def is_supported_format(self, document_path: Path) -> bool:
        """
        Check if document format is supported.
        
        Args:
            document_path: Path to document file
            
        Returns:
            True if format is supported, False otherwise
        """
        return document_path.suffix.lower() in self.supported_formats
    
    def _validate_file(self, document_path: Path) -> None:
        """Validate file exists and is readable."""
        if not document_path.exists():
            raise DocumentProcessingError(f"File does not exist: {document_path}")
        
        if not document_path.is_file():
            raise DocumentProcessingError(f"Path is not a file: {document_path}")
        
        if document_path.stat().st_size == 0:
            raise DocumentProcessingError(f"File is empty: {document_path}")
        
        if document_path.stat().st_size > self.max_file_size:
            raise DocumentProcessingError(f"File too large: {document_path.stat().st_size} bytes")
        
        if not self.is_supported_format(document_path):
            raise DocumentProcessingError(f"Unsupported format: {document_path.suffix}")
    
    def _extract_pdf_pages(self, pdf_path: Path) -> List[PageInfo]:
        """Extract pages from PDF document."""
        pages = []
        
        try:
            doc = fitz.open(str(pdf_path))
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Get page dimensions
                rect = page.rect
                width = int(rect.width)
                height = int(rect.height)
                
                # Extract text content
                text_content = page.get_text()
                
                # Convert page to image for visual processing
                mat = fitz.Matrix(self.default_dpi / 72, self.default_dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Create page info
                page_info = PageInfo(
                    page_number=page_num,
                    width=width,
                    height=height,
                    dpi=self.default_dpi,
                    rotation=page.rotation,
                    text_content=text_content,
                    metadata={
                        'pdf_page_number': page_num,
                        'original_width': rect.width,
                        'original_height': rect.height,
                        'has_text': bool(text_content.strip()),
                        'image_size': len(img_data)
                    }
                )
                
                pages.append(page_info)
            
            doc.close()
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to extract PDF pages: {str(e)}") from e
        
        return pages
    
    def _extract_image_pages(self, image_path: Path) -> List[PageInfo]:
        """Extract page from image document."""
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                width, height = img.size
                
                # Get DPI if available
                dpi = img.info.get('dpi', (72, 72))
                if isinstance(dpi, tuple):
                    dpi = dpi[0]
                
                # Create single page info
                page_info = PageInfo(
                    page_number=0,
                    width=width,
                    height=height,
                    dpi=float(dpi),
                    rotation=0,
                    text_content=None,  # Images don't have extractable text
                    metadata={
                        'image_mode': img.mode,
                        'image_format': img.format,
                        'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info,
                        'color_depth': len(img.getbands()) * 8 if hasattr(img, 'getbands') else 24
                    }
                )
                
                return [page_info]
                
        except Exception as e:
            raise DocumentProcessingError(f"Failed to extract image page: {str(e)}") from e
    
    def _extract_pdf_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """Extract PDF-specific metadata."""
        try:
            doc = fitz.open(str(pdf_path))
            metadata = doc.metadata
            
            pdf_metadata = {
                'page_count': len(doc),
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
                'producer': metadata.get('producer', ''),
                'creation_date': metadata.get('creationDate', ''),
                'modification_date': metadata.get('modDate', ''),
                'encrypted': doc.needs_pass,
                'pdf_version': doc.pdf_version()
            }
            
            doc.close()
            return pdf_metadata
            
        except Exception as e:
            self.logger.warning(f"Failed to extract PDF metadata: {str(e)}")
            return {'page_count': 0}
    
    def _extract_image_metadata(self, image_path: Path) -> Dict[str, Any]:
        """Extract image-specific metadata."""
        try:
            with Image.open(image_path) as img:
                return {
                    'page_count': 1,
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'image_format': img.format,  # Use different key to avoid overriding main format
                    'dpi': img.info.get('dpi', (72, 72)),
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
        except Exception as e:
            self.logger.warning(f"Failed to extract image metadata: {str(e)}")
            return {'page_count': 1}
    
    def _analyze_document_structure(self, document: Document) -> Dict[str, Any]:
        """Analyze document structure and layout."""
        structure = {
            'total_pages': document.page_count,
            'page_sizes': [],
            'text_distribution': [],
            'layout_analysis': {}
        }
        
        for page in document.pages:
            # Page size info
            structure['page_sizes'].append({
                'page': page.page_number,
                'width': page.width,
                'height': page.height,
                'area': page.area,
                'aspect_ratio': page.aspect_ratio
            })
            
            # Text distribution
            text_info = {
                'page': page.page_number,
                'has_text': bool(page.text_content and page.text_content.strip()),
                'text_length': len(page.text_content) if page.text_content else 0,
                'estimated_words': len(page.text_content.split()) if page.text_content else 0
            }
            structure['text_distribution'].append(text_info)
        
        # Overall layout analysis
        if document.pages:
            avg_width = sum(p.width for p in document.pages) / len(document.pages)
            avg_height = sum(p.height for p in document.pages) / len(document.pages)
            
            structure['layout_analysis'] = {
                'average_page_size': (avg_width, avg_height),
                'consistent_sizing': self._check_consistent_page_sizes(document.pages),
                'orientation': self._determine_document_orientation(document.pages),
                'total_text_content': sum(len(p.text_content) if p.text_content else 0 for p in document.pages),
                'pages_with_text': sum(1 for p in document.pages if p.text_content and p.text_content.strip())
            }
        
        return structure
    
    def _check_consistent_page_sizes(self, pages: List[PageInfo]) -> bool:
        """Check if all pages have consistent dimensions."""
        if not pages:
            return True
        
        first_page = pages[0]
        tolerance = 10  # pixels
        
        for page in pages[1:]:
            if (abs(page.width - first_page.width) > tolerance or 
                abs(page.height - first_page.height) > tolerance):
                return False
        
        return True
    
    def _determine_document_orientation(self, pages: List[PageInfo]) -> str:
        """Determine primary document orientation."""
        if not pages:
            return 'unknown'
        
        portrait_count = sum(1 for p in pages if p.height > p.width)
        landscape_count = sum(1 for p in pages if p.width > p.height)
        square_count = len(pages) - portrait_count - landscape_count
        
        if portrait_count > landscape_count and portrait_count > square_count:
            return 'portrait'
        elif landscape_count > portrait_count and landscape_count > square_count:
            return 'landscape'
        else:
            return 'mixed'