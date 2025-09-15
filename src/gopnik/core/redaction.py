"""
Redaction engine for applying redactions while preserving document layout.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import io
import re

from .interfaces import RedactionEngineInterface
from ..models.pii import PIIDetection, PIIType
from ..models.profiles import RedactionProfile, RedactionStyle
from ..models.processing import Document, DocumentFormat
from ..models.errors import DocumentProcessingError


class RedactionEngine(RedactionEngineInterface):
    """
    Applies redactions to documents while preserving layout and structure.
    
    Handles coordinate-based redaction for both visual and text elements,
    supporting different redaction styles and patterns.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.temp_dir = Path(tempfile.gettempdir()) / "gopnik_redaction"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Redaction style configurations
        self.style_configs = {
            RedactionStyle.SOLID_BLACK: {
                'color': (0, 0, 0),
                'pattern': None,
                'opacity': 255
            },
            RedactionStyle.SOLID_WHITE: {
                'color': (255, 255, 255),
                'pattern': None,
                'opacity': 255
            },
            RedactionStyle.PIXELATED: {
                'color': None,
                'pattern': 'pixelate',
                'opacity': 255
            },
            RedactionStyle.BLURRED: {
                'color': None,
                'pattern': 'blur',
                'opacity': 255
            }
        }
    
    def apply_redactions(self, document_path: Path, detections: List[PIIDetection], 
                        profile: RedactionProfile) -> Path:
        """
        Apply redactions to document based on detections and profile.
        
        Args:
            document_path: Path to original document
            detections: List of PII detections to redact
            profile: Redaction profile with style settings
            
        Returns:
            Path to redacted document
            
        Raises:
            DocumentProcessingError: If redaction fails
        """
        try:
            self.logger.info(f"Applying redactions to {document_path} with {len(detections)} detections")
            
            # Validate inputs
            if not document_path.exists():
                raise DocumentProcessingError(f"Document not found: {document_path}")
            
            if not detections:
                self.logger.warning("No detections provided, returning copy of original")
                return self._create_copy(document_path)
            
            # Filter detections based on profile
            filtered_detections = self._filter_detections_by_profile(detections, profile)
            
            if not filtered_detections:
                self.logger.info("No detections match profile criteria, returning copy of original")
                return self._create_copy(document_path)
            
            # Determine document format and apply appropriate redaction
            doc_format = DocumentFormat.from_path(document_path)
            
            if doc_format == DocumentFormat.PDF:
                return self._apply_pdf_redactions(document_path, filtered_detections, profile)
            else:
                return self._apply_image_redactions(document_path, filtered_detections, profile)
                
        except Exception as e:
            self.logger.error(f"Failed to apply redactions: {str(e)}")
            raise DocumentProcessingError(f"Redaction failed: {str(e)}") from e
    
    def preserve_layout(self) -> bool:
        """
        Return whether this engine preserves document layout.
        
        Returns:
            True - this engine preserves layout
        """
        return True
    
    def _filter_detections_by_profile(self, detections: List[PIIDetection], 
                                    profile: RedactionProfile) -> List[PIIDetection]:
        """Filter detections based on profile settings."""
        filtered = []
        
        for detection in detections:
            # Check if PII type should be redacted according to profile
            pii_type_str = detection.type.value
            should_redact = profile.is_pii_type_enabled(pii_type_str)
            
            if should_redact:
                # Check confidence threshold
                if detection.confidence >= profile.confidence_threshold:
                    filtered.append(detection)
                else:
                    self.logger.debug(f"Skipping {detection.type.value} detection due to low confidence: {detection.confidence}")
            else:
                self.logger.debug(f"Skipping {detection.type.value} detection - not configured for redaction")
        
        return filtered
    
    def _create_copy(self, document_path: Path) -> Path:
        """Create a copy of the document in temp directory."""
        output_path = self.temp_dir / f"redacted_{document_path.name}"
        shutil.copy2(document_path, output_path)
        return output_path
    
    def _apply_pdf_redactions(self, pdf_path: Path, detections: List[PIIDetection], 
                            profile: RedactionProfile) -> Path:
        """Apply redactions to PDF document."""
        output_path = self.temp_dir / f"redacted_{pdf_path.name}"
        
        try:
            # Open PDF document
            doc = fitz.open(str(pdf_path))
            
            # Group detections by page
            detections_by_page = self._group_detections_by_page(detections)
            
            # Apply redactions page by page
            for page_num, page_detections in detections_by_page.items():
                if page_num < len(doc):
                    page = doc.load_page(page_num)
                    self._apply_pdf_page_redactions(page, page_detections, profile)
            
            # Save redacted document
            doc.save(str(output_path))
            doc.close()
            
            self.logger.info(f"Successfully applied PDF redactions to {output_path}")
            return output_path
            
        except Exception as e:
            raise DocumentProcessingError(f"PDF redaction failed: {str(e)}") from e
    
    def _apply_image_redactions(self, image_path: Path, detections: List[PIIDetection], 
                              profile: RedactionProfile) -> Path:
        """Apply redactions to image document."""
        output_path = self.temp_dir / f"redacted_{image_path.name}"
        
        try:
            # Open image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Create a copy for redaction
                redacted_img = img.copy()
                
                # Apply redactions
                for detection in detections:
                    if detection.page_number == 0:  # Images are single page
                        redacted_img = self._apply_image_detection_redaction(
                            redacted_img, detection, profile
                        )
                
                # Save redacted image
                redacted_img.save(output_path, quality=95, optimize=True)
            
            self.logger.info(f"Successfully applied image redactions to {output_path}")
            return output_path
            
        except Exception as e:
            raise DocumentProcessingError(f"Image redaction failed: {str(e)}") from e
    
    def _group_detections_by_page(self, detections: List[PIIDetection]) -> Dict[int, List[PIIDetection]]:
        """Group detections by page number."""
        grouped = {}
        for detection in detections:
            page_num = detection.page_number
            if page_num not in grouped:
                grouped[page_num] = []
            grouped[page_num].append(detection)
        return grouped
    
    def _apply_pdf_page_redactions(self, page: fitz.Page, detections: List[PIIDetection], 
                                 profile: RedactionProfile) -> None:
        """Apply redactions to a single PDF page."""
        for detection in detections:
            # Convert coordinates to PDF coordinate system
            bbox = detection.bounding_box
            rect = fitz.Rect(bbox.x1, bbox.y1, bbox.x2, bbox.y2)
            
            # Apply redaction based on profile style
            if profile.redaction_style == RedactionStyle.SOLID_BLACK:
                page.add_redact_annot(rect, fill=(0, 0, 0))
            elif profile.redaction_style == RedactionStyle.SOLID_WHITE:
                page.add_redact_annot(rect, fill=(1, 1, 1))
            else:
                # For other styles, use black as fallback
                page.add_redact_annot(rect, fill=(0, 0, 0))
        
        # Apply all redactions
        page.apply_redactions()
    
    def _apply_image_detection_redaction(self, img: Image.Image, detection: PIIDetection, 
                                       profile: RedactionProfile) -> Image.Image:
        """Apply redaction to a single detection in an image."""
        bbox = detection.bounding_box
        style_config = self.style_configs.get(profile.redaction_style, self.style_configs[RedactionStyle.SOLID_BLACK])
        
        # Create drawing context
        draw = ImageDraw.Draw(img)
        
        # Apply redaction based on style
        if style_config['pattern'] is None:
            # Solid color redaction
            color = style_config['color']
            draw.rectangle([bbox.x1, bbox.y1, bbox.x2, bbox.y2], fill=color)
            
        elif style_config['pattern'] == 'pixelate':
            # Pixelated redaction
            img = self._apply_pixelation(img, bbox)
            
        elif style_config['pattern'] == 'blur':
            # Blurred redaction
            img = self._apply_blur(img, bbox)
        
        return img
    
    def _apply_pixelation(self, img: Image.Image, bbox) -> Image.Image:
        """Apply pixelation effect to a region."""
        # Extract region
        region = img.crop((bbox.x1, bbox.y1, bbox.x2, bbox.y2))
        
        # Pixelate by downscaling and upscaling
        pixel_size = max(8, min(bbox.width, bbox.height) // 8)
        small_size = (max(1, bbox.width // pixel_size), max(1, bbox.height // pixel_size))
        
        # Downsample and upsample
        pixelated = region.resize(small_size, Image.NEAREST)
        pixelated = pixelated.resize((bbox.width, bbox.height), Image.NEAREST)
        
        # Paste back
        img.paste(pixelated, (bbox.x1, bbox.y1))
        return img
    
    def _apply_blur(self, img: Image.Image, bbox) -> Image.Image:
        """Apply blur effect to a region."""
        from PIL import ImageFilter
        
        # Extract region
        region = img.crop((bbox.x1, bbox.y1, bbox.x2, bbox.y2))
        
        # Apply blur
        blur_radius = max(5, min(bbox.width, bbox.height) // 10)
        blurred = region.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # Paste back
        img.paste(blurred, (bbox.x1, bbox.y1))
        return img
    
    def _apply_visual_redaction(self, image_data: bytes, detection: PIIDetection, 
                               profile: RedactionProfile) -> bytes:
        """
        Apply redaction to visual elements in image data.
        
        Args:
            image_data: Raw image data
            detection: PII detection with coordinates
            profile: Redaction profile with style settings
            
        Returns:
            Modified image data with redaction applied
        """
        try:
            # Convert bytes to PIL Image
            img = Image.open(io.BytesIO(image_data))
            
            # Apply redaction
            redacted_img = self._apply_image_detection_redaction(img, detection, profile)
            
            # Convert back to bytes
            output_buffer = io.BytesIO()
            redacted_img.save(output_buffer, format='PNG')
            return output_buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Visual redaction failed: {str(e)}")
            return image_data  # Return original on error
    
    def _apply_text_redaction(self, text_content: str, detection: PIIDetection,
                             profile: RedactionProfile) -> str:
        """
        Apply redaction to text content.
        
        Args:
            text_content: Original text content
            detection: PII detection with text information
            profile: Redaction profile with style settings
            
        Returns:
            Modified text content with redaction applied
        """
        if not detection.text_content:
            return text_content
        
        pii_type_str = detection.type.value
        if not profile.is_pii_type_enabled(pii_type_str):
            return text_content
        
        # Get replacement pattern
        replacement = self._get_text_replacement(detection.type, detection.text_content, profile)
        
        # Replace the detected text
        try:
            # Use regex for more robust replacement
            escaped_text = re.escape(detection.text_content)
            pattern = re.compile(escaped_text, re.IGNORECASE)
            redacted_text = pattern.sub(replacement, text_content)
            
            return redacted_text
            
        except Exception as e:
            self.logger.warning(f"Text redaction failed for '{detection.text_content}': {str(e)}")
            return text_content
    
    def _get_text_replacement(self, pii_type: PIIType, original_text: str, profile: RedactionProfile) -> str:
        """Get appropriate replacement text for PII type."""
        # Check if profile specifies custom replacement in custom_rules
        pii_type_str = pii_type.value
        if pii_type_str in profile.custom_rules and 'replacement_text' in profile.custom_rules[pii_type_str]:
            return profile.custom_rules[pii_type_str]['replacement_text']
        
        # Default replacements based on PII type
        replacements = {
            PIIType.NAME: "[NAME REDACTED]",
            PIIType.EMAIL: "[EMAIL REDACTED]",
            PIIType.PHONE: "[PHONE REDACTED]",
            PIIType.ADDRESS: "[ADDRESS REDACTED]",
            PIIType.SSN: "[SSN REDACTED]",
            PIIType.ID_NUMBER: "[ID REDACTED]",
            PIIType.CREDIT_CARD: "[CARD REDACTED]",
            PIIType.DATE_OF_BIRTH: "[DOB REDACTED]",
            PIIType.PASSPORT_NUMBER: "[PASSPORT REDACTED]",
            PIIType.DRIVER_LICENSE: "[LICENSE REDACTED]",
            PIIType.MEDICAL_RECORD_NUMBER: "[MEDICAL ID REDACTED]",
            PIIType.INSURANCE_ID: "[INSURANCE ID REDACTED]",
            PIIType.BANK_ACCOUNT: "[ACCOUNT REDACTED]",
            PIIType.IP_ADDRESS: "[IP REDACTED]"
        }
        
        # For visual PII, use generic redaction
        if pii_type in PIIType.visual_types():
            return "[REDACTED]"
        
        return replacements.get(pii_type, "[REDACTED]")
    
    def get_redaction_statistics(self, detections: List[PIIDetection], 
                               profile: RedactionProfile) -> Dict[str, Any]:
        """
        Get statistics about redactions that would be applied.
        
        Args:
            detections: List of PII detections
            profile: Redaction profile
            
        Returns:
            Dictionary with redaction statistics
        """
        filtered_detections = self._filter_detections_by_profile(detections, profile)
        
        stats = {
            'total_detections': len(detections),
            'redacted_detections': len(filtered_detections),
            'skipped_detections': len(detections) - len(filtered_detections),
            'redaction_by_type': {},
            'redaction_by_page': {},
            'redaction_style': profile.redaction_style.value
        }
        
        # Count by type
        for detection in filtered_detections:
            pii_type = detection.type.value
            stats['redaction_by_type'][pii_type] = stats['redaction_by_type'].get(pii_type, 0) + 1
            
            # Count by page
            page_num = detection.page_number
            stats['redaction_by_page'][page_num] = stats['redaction_by_page'].get(page_num, 0) + 1
        
        return stats