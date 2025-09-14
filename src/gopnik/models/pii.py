"""
PII detection data models and types.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Optional, Dict, Any, List, Union
import json
import uuid
from datetime import datetime


class PIIType(Enum):
    """Enumeration of supported PII types."""
    # Visual PII types
    FACE = "face"
    SIGNATURE = "signature"
    BARCODE = "barcode"
    QR_CODE = "qr_code"
    
    # Text PII types
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    SSN = "ssn"
    ID_NUMBER = "id_number"
    CREDIT_CARD = "credit_card"
    DATE_OF_BIRTH = "date_of_birth"
    
    # Additional PII types
    PASSPORT_NUMBER = "passport_number"
    DRIVER_LICENSE = "driver_license"
    MEDICAL_RECORD_NUMBER = "medical_record_number"
    INSURANCE_ID = "insurance_id"
    BANK_ACCOUNT = "bank_account"
    IP_ADDRESS = "ip_address"
    
    @classmethod
    def visual_types(cls) -> List['PIIType']:
        """Get list of visual PII types."""
        return [cls.FACE, cls.SIGNATURE, cls.BARCODE, cls.QR_CODE]
    
    @classmethod
    def text_types(cls) -> List['PIIType']:
        """Get list of text PII types."""
        return [pii_type for pii_type in cls if pii_type not in cls.visual_types()]
    
    @classmethod
    def sensitive_types(cls) -> List['PIIType']:
        """Get list of highly sensitive PII types."""
        return [
            cls.SSN, cls.CREDIT_CARD, cls.PASSPORT_NUMBER, 
            cls.DRIVER_LICENSE, cls.MEDICAL_RECORD_NUMBER,
            cls.BANK_ACCOUNT
        ]


@dataclass
class BoundingBox:
    """
    Represents a bounding box with coordinate validation and utility methods.
    
    Attributes:
        x1: Left coordinate
        y1: Top coordinate  
        x2: Right coordinate
        y2: Bottom coordinate
    """
    x1: int
    y1: int
    x2: int
    y2: int
    
    def __post_init__(self):
        """Validate bounding box coordinates."""
        if self.x1 >= self.x2:
            raise ValueError(f"x1 ({self.x1}) must be less than x2 ({self.x2})")
        if self.y1 >= self.y2:
            raise ValueError(f"y1 ({self.y1}) must be less than y2 ({self.y2})")
        if any(coord < 0 for coord in [self.x1, self.y1, self.x2, self.y2]):
            raise ValueError(f"Coordinates cannot be negative: ({self.x1}, {self.y1}, {self.x2}, {self.y2})")
    
    @property
    def width(self) -> int:
        """Get width of bounding box."""
        return self.x2 - self.x1
    
    @property
    def height(self) -> int:
        """Get height of bounding box."""
        return self.y2 - self.y1
    
    @property
    def area(self) -> int:
        """Get area of bounding box."""
        return self.width * self.height
    
    @property
    def center(self) -> Tuple[float, float]:
        """Get center point of bounding box."""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    def to_tuple(self) -> Tuple[int, int, int, int]:
        """Convert to tuple format (x1, y1, x2, y2)."""
        return (self.x1, self.y1, self.x2, self.y2)
    
    @classmethod
    def from_tuple(cls, coords: Tuple[int, int, int, int]) -> 'BoundingBox':
        """Create BoundingBox from tuple."""
        return cls(coords[0], coords[1], coords[2], coords[3])
    
    def overlaps_with(self, other: 'BoundingBox', threshold: float = 0.0) -> bool:
        """
        Check if this bounding box overlaps with another.
        
        Args:
            other: Another bounding box
            threshold: Minimum overlap ratio (0.0 to 1.0)
            
        Returns:
            True if boxes overlap above threshold
        """
        x1_max = max(self.x1, other.x1)
        y1_max = max(self.y1, other.y1)
        x2_min = min(self.x2, other.x2)
        y2_min = min(self.y2, other.y2)
        
        if x1_max >= x2_min or y1_max >= y2_min:
            return False
        
        overlap_area = (x2_min - x1_max) * (y2_min - y1_max)
        
        if threshold == 0.0:
            return overlap_area > 0
        
        union_area = self.area + other.area - overlap_area
        return (overlap_area / union_area) >= threshold if union_area > 0 else False
    
    def intersection_over_union(self, other: 'BoundingBox') -> float:
        """
        Calculate Intersection over Union (IoU) with another bounding box.
        
        Args:
            other: Another bounding box
            
        Returns:
            IoU score between 0.0 and 1.0
        """
        x1_max = max(self.x1, other.x1)
        y1_max = max(self.y1, other.y1)
        x2_min = min(self.x2, other.x2)
        y2_min = min(self.y2, other.y2)
        
        if x1_max >= x2_min or y1_max >= y2_min:
            return 0.0
        
        intersection = (x2_min - x1_max) * (y2_min - y1_max)
        union = self.area + other.area - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def expand(self, margin: int) -> 'BoundingBox':
        """
        Expand bounding box by given margin.
        
        Args:
            margin: Pixels to expand in all directions
            
        Returns:
            New expanded bounding box
        """
        return BoundingBox(
            max(0, self.x1 - margin),
            max(0, self.y1 - margin),
            self.x2 + margin,
            self.y2 + margin
        )
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format."""
        return {
            'x1': self.x1,
            'y1': self.y1,
            'x2': self.x2,
            'y2': self.y2,
            'width': self.width,
            'height': self.height,
            'area': self.area
        }


@dataclass
class PIIDetection:
    """
    Represents a detected PII element in a document.
    
    Attributes:
        id: Unique identifier for this detection
        type: Type of PII detected
        bounding_box: Bounding box coordinates
        confidence: Detection confidence score (0.0 to 1.0)
        text_content: Actual text content if applicable
        page_number: Page number where detection was found (0-indexed)
        detection_method: Method used for detection (cv, nlp, hybrid)
        timestamp: When detection was created
        metadata: Additional detection metadata
    """
    type: PIIType
    bounding_box: BoundingBox
    confidence: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    text_content: Optional[str] = None
    page_number: int = 0
    detection_method: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate detection data after initialization."""
        self._validate_confidence()
        self._validate_page_number()
        self._validate_detection_method()
        self._validate_text_content()
    
    def _validate_confidence(self):
        """Validate confidence score."""
        if not isinstance(self.confidence, (int, float)):
            raise TypeError(f"Confidence must be a number, got {type(self.confidence)}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
    
    def _validate_page_number(self):
        """Validate page number."""
        if not isinstance(self.page_number, int):
            raise TypeError(f"Page number must be an integer, got {type(self.page_number)}")
        if self.page_number < 0:
            raise ValueError(f"Page number cannot be negative, got {self.page_number}")
    
    def _validate_detection_method(self):
        """Validate detection method."""
        valid_methods = ["cv", "nlp", "hybrid", "manual", "unknown"]
        if self.detection_method not in valid_methods:
            raise ValueError(f"Detection method must be one of {valid_methods}, got {self.detection_method}")
    
    def _validate_text_content(self):
        """Validate text content based on PII type."""
        if self.type in PIIType.visual_types() and self.text_content is not None:
            # Visual PII types shouldn't have text content unless it's extracted text
            if not self.metadata.get('extracted_text', False):
                self.text_content = None
        
        if self.type in PIIType.text_types() and self.text_content is None:
            # Text PII types should have text content
            pass  # Allow None for now, but could be stricter
    
    # Legacy property for backward compatibility
    @property
    def coordinates(self) -> Tuple[int, int, int, int]:
        """Get coordinates as tuple (for backward compatibility)."""
        return self.bounding_box.to_tuple()
    
    @property
    def width(self) -> int:
        """Get width of detection bounding box."""
        return self.bounding_box.width
    
    @property
    def height(self) -> int:
        """Get height of detection bounding box."""
        return self.bounding_box.height
    
    @property
    def area(self) -> int:
        """Get area of detection bounding box."""
        return self.bounding_box.area
    
    @property
    def center(self) -> Tuple[float, float]:
        """Get center point of detection."""
        return self.bounding_box.center
    
    @property
    def is_visual_pii(self) -> bool:
        """Check if this is a visual PII type."""
        return self.type in PIIType.visual_types()
    
    @property
    def is_text_pii(self) -> bool:
        """Check if this is a text PII type."""
        return self.type in PIIType.text_types()
    
    @property
    def is_sensitive(self) -> bool:
        """Check if this is a sensitive PII type."""
        return self.type in PIIType.sensitive_types()
    
    def overlaps_with(self, other: 'PIIDetection', threshold: float = 0.5) -> bool:
        """
        Check if this detection overlaps with another detection.
        
        Args:
            other: Another PII detection
            threshold: Minimum overlap ratio to consider as overlap
            
        Returns:
            True if detections overlap above threshold
        """
        return self.bounding_box.overlaps_with(other.bounding_box, threshold)
    
    def intersection_over_union(self, other: 'PIIDetection') -> float:
        """
        Calculate Intersection over Union (IoU) with another detection.
        
        Args:
            other: Another PII detection
            
        Returns:
            IoU score between 0.0 and 1.0
        """
        return self.bounding_box.intersection_over_union(other.bounding_box)
    
    def is_duplicate_of(self, other: 'PIIDetection', iou_threshold: float = 0.7) -> bool:
        """
        Check if this detection is likely a duplicate of another.
        
        Args:
            other: Another PII detection
            iou_threshold: IoU threshold for considering duplicates
            
        Returns:
            True if detections are likely duplicates
        """
        if self.type != other.type:
            return False
        
        if self.page_number != other.page_number:
            return False
        
        iou = self.intersection_over_union(other)
        return iou >= iou_threshold
    
    def merge_with(self, other: 'PIIDetection') -> 'PIIDetection':
        """
        Merge this detection with another detection.
        
        Args:
            other: Another PII detection to merge with
            
        Returns:
            New merged detection
        """
        if not self.is_duplicate_of(other):
            raise ValueError("Cannot merge non-duplicate detections")
        
        # Use detection with higher confidence
        primary = self if self.confidence >= other.confidence else other
        secondary = other if self.confidence >= other.confidence else self
        
        # Merge bounding boxes (use union)
        merged_bbox = BoundingBox(
            min(self.bounding_box.x1, other.bounding_box.x1),
            min(self.bounding_box.y1, other.bounding_box.y1),
            max(self.bounding_box.x2, other.bounding_box.x2),
            max(self.bounding_box.y2, other.bounding_box.y2)
        )
        
        # Merge metadata
        merged_metadata = {**secondary.metadata, **primary.metadata}
        merged_metadata['merged_from'] = [self.id, other.id]
        merged_metadata['merged_confidences'] = [self.confidence, other.confidence]
        
        return PIIDetection(
            type=primary.type,
            bounding_box=merged_bbox,
            confidence=max(self.confidence, other.confidence),
            text_content=primary.text_content or secondary.text_content,
            page_number=primary.page_number,
            detection_method="hybrid" if self.detection_method != other.detection_method else primary.detection_method,
            metadata=merged_metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert detection to dictionary format.
        
        Returns:
            Dictionary representation of detection
        """
        return {
            'id': self.id,
            'type': self.type.value,
            'bounding_box': self.bounding_box.to_dict(),
            'confidence': self.confidence,
            'text_content': self.text_content,
            'page_number': self.page_number,
            'detection_method': self.detection_method,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
            # Legacy fields for backward compatibility
            'coordinates': self.coordinates,
            'width': self.width,
            'height': self.height,
            'area': self.area
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PIIDetection':
        """
        Create detection from dictionary data.
        
        Args:
            data: Dictionary containing detection data
            
        Returns:
            PIIDetection instance
        """
        # Handle both new and legacy coordinate formats
        if 'bounding_box' in data:
            bbox_data = data['bounding_box']
            bounding_box = BoundingBox(
                bbox_data['x1'], bbox_data['y1'],
                bbox_data['x2'], bbox_data['y2']
            )
        elif 'coordinates' in data:
            coords = data['coordinates']
            bounding_box = BoundingBox.from_tuple(coords)
        else:
            raise ValueError("Missing bounding box or coordinates data")
        
        # Parse timestamp
        timestamp_str = data.get('timestamp')
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            type=PIIType(data['type']),
            bounding_box=bounding_box,
            confidence=data['confidence'],
            text_content=data.get('text_content'),
            page_number=data.get('page_number', 0),
            detection_method=data.get('detection_method', 'unknown'),
            timestamp=timestamp,
            metadata=data.get('metadata', {})
        )
    
    def to_json(self) -> str:
        """
        Convert detection to JSON string.
        
        Returns:
            JSON representation of detection
        """
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PIIDetection':
        """
        Create detection from JSON string.
        
        Args:
            json_str: JSON string containing detection data
            
        Returns:
            PIIDetection instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

@dataclass
class PIIDetectionCollection:
    """
    Collection of PII detections with utility methods for processing and analysis.
    
    Attributes:
        detections: List of PII detections
        document_id: ID of the document these detections belong to
        total_pages: Total number of pages in the document
        processing_metadata: Metadata about the detection process
    """
    detections: List[PIIDetection] = field(default_factory=list)
    document_id: Optional[str] = None
    total_pages: int = 1
    processing_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        """Get number of detections."""
        return len(self.detections)
    
    def __iter__(self):
        """Iterate over detections."""
        return iter(self.detections)
    
    def __getitem__(self, index: int) -> PIIDetection:
        """Get detection by index."""
        return self.detections[index]
    
    def add_detection(self, detection: PIIDetection) -> None:
        """Add a detection to the collection."""
        self.detections.append(detection)
    
    def remove_detection(self, detection_id: str) -> bool:
        """
        Remove a detection by ID.
        
        Args:
            detection_id: ID of detection to remove
            
        Returns:
            True if detection was found and removed
        """
        for i, detection in enumerate(self.detections):
            if detection.id == detection_id:
                del self.detections[i]
                return True
        return False
    
    def get_by_type(self, pii_type: PIIType) -> List[PIIDetection]:
        """Get all detections of a specific type."""
        return [d for d in self.detections if d.type == pii_type]
    
    def get_by_page(self, page_number: int) -> List[PIIDetection]:
        """Get all detections on a specific page."""
        return [d for d in self.detections if d.page_number == page_number]
    
    def get_high_confidence(self, threshold: float = 0.8) -> List[PIIDetection]:
        """Get detections above confidence threshold."""
        return [d for d in self.detections if d.confidence >= threshold]
    
    def get_visual_detections(self) -> List[PIIDetection]:
        """Get all visual PII detections."""
        return [d for d in self.detections if d.is_visual_pii]
    
    def get_text_detections(self) -> List[PIIDetection]:
        """Get all text PII detections."""
        return [d for d in self.detections if d.is_text_pii]
    
    def get_sensitive_detections(self) -> List[PIIDetection]:
        """Get all sensitive PII detections."""
        return [d for d in self.detections if d.is_sensitive]
    
    def remove_duplicates(self, iou_threshold: float = 0.7) -> int:
        """
        Remove duplicate detections based on IoU threshold.
        
        Args:
            iou_threshold: IoU threshold for considering duplicates
            
        Returns:
            Number of duplicates removed
        """
        original_count = len(self.detections)
        unique_detections = []
        
        for detection in self.detections:
            is_duplicate = False
            for unique_detection in unique_detections:
                if detection.is_duplicate_of(unique_detection, iou_threshold):
                    # Merge with existing detection if confidence is higher
                    if detection.confidence > unique_detection.confidence:
                        # Replace the unique detection with merged version
                        merged = detection.merge_with(unique_detection)
                        unique_detections = [d for d in unique_detections if d.id != unique_detection.id]
                        unique_detections.append(merged)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_detections.append(detection)
        
        self.detections = unique_detections
        return original_count - len(self.detections)
    
    def filter_by_confidence(self, min_confidence: float) -> None:
        """Filter detections by minimum confidence."""
        self.detections = [d for d in self.detections if d.confidence >= min_confidence]
    
    def sort_by_confidence(self, descending: bool = True) -> None:
        """Sort detections by confidence score."""
        self.detections.sort(key=lambda d: d.confidence, reverse=descending)
    
    def sort_by_area(self, descending: bool = True) -> None:
        """Sort detections by bounding box area."""
        self.detections.sort(key=lambda d: d.area, reverse=descending)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the detection collection.
        
        Returns:
            Dictionary with detection statistics
        """
        if not self.detections:
            return {
                'total_detections': 0,
                'by_type': {},
                'by_page': {},
                'confidence_stats': {},
                'area_stats': {}
            }
        
        # Count by type
        type_counts = {}
        for detection in self.detections:
            type_name = detection.type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        # Count by page
        page_counts = {}
        for detection in self.detections:
            page_counts[detection.page_number] = page_counts.get(detection.page_number, 0) + 1
        
        # Confidence statistics
        confidences = [d.confidence for d in self.detections]
        confidence_stats = {
            'min': min(confidences),
            'max': max(confidences),
            'mean': sum(confidences) / len(confidences),
            'high_confidence_count': len([c for c in confidences if c >= 0.8])
        }
        
        # Area statistics
        areas = [d.area for d in self.detections]
        area_stats = {
            'min': min(areas),
            'max': max(areas),
            'mean': sum(areas) / len(areas),
            'total': sum(areas)
        }
        
        return {
            'total_detections': len(self.detections),
            'by_type': type_counts,
            'by_page': page_counts,
            'confidence_stats': confidence_stats,
            'area_stats': area_stats,
            'visual_count': len(self.get_visual_detections()),
            'text_count': len(self.get_text_detections()),
            'sensitive_count': len(self.get_sensitive_detections())
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert collection to dictionary format."""
        return {
            'document_id': self.document_id,
            'total_pages': self.total_pages,
            'processing_metadata': self.processing_metadata,
            'detections': [d.to_dict() for d in self.detections],
            'statistics': self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PIIDetectionCollection':
        """Create collection from dictionary data."""
        detections = [PIIDetection.from_dict(d) for d in data.get('detections', [])]
        
        return cls(
            detections=detections,
            document_id=data.get('document_id'),
            total_pages=data.get('total_pages', 1),
            processing_metadata=data.get('processing_metadata', {})
        )
    
    def to_json(self) -> str:
        """Convert collection to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PIIDetectionCollection':
        """Create collection from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Utility functions for PII detection validation and processing

def validate_detection_confidence(confidence: float) -> bool:
    """
    Validate detection confidence score.
    
    Args:
        confidence: Confidence score to validate
        
    Returns:
        True if valid confidence score
    """
    return isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0


def validate_coordinates(coordinates: Union[Tuple[int, int, int, int], BoundingBox]) -> bool:
    """
    Validate coordinate data.
    
    Args:
        coordinates: Coordinates to validate (tuple or BoundingBox)
        
    Returns:
        True if valid coordinates
    """
    try:
        if isinstance(coordinates, tuple):
            BoundingBox.from_tuple(coordinates)
        elif isinstance(coordinates, BoundingBox):
            # BoundingBox validates itself in __post_init__
            pass
        else:
            return False
        return True
    except (ValueError, TypeError):
        return False


def merge_overlapping_detections(
    detections: List[PIIDetection], 
    iou_threshold: float = 0.7
) -> List[PIIDetection]:
    """
    Merge overlapping detections in a list.
    
    Args:
        detections: List of PII detections
        iou_threshold: IoU threshold for merging
        
    Returns:
        List of merged detections
    """
    collection = PIIDetectionCollection(detections=detections.copy())
    collection.remove_duplicates(iou_threshold)
    return collection.detections


def filter_detections_by_confidence(
    detections: List[PIIDetection], 
    min_confidence: float
) -> List[PIIDetection]:
    """
    Filter detections by minimum confidence threshold.
    
    Args:
        detections: List of PII detections
        min_confidence: Minimum confidence threshold
        
    Returns:
        Filtered list of detections
    """
    return [d for d in detections if d.confidence >= min_confidence]


def group_detections_by_type(detections: List[PIIDetection]) -> Dict[PIIType, List[PIIDetection]]:
    """
    Group detections by PII type.
    
    Args:
        detections: List of PII detections
        
    Returns:
        Dictionary mapping PII types to detection lists
    """
    groups = {}
    for detection in detections:
        if detection.type not in groups:
            groups[detection.type] = []
        groups[detection.type].append(detection)
    return groups


def calculate_detection_coverage(
    detections: List[PIIDetection], 
    document_area: int
) -> float:
    """
    Calculate what percentage of document area is covered by detections.
    
    Args:
        detections: List of PII detections
        document_area: Total document area in pixels
        
    Returns:
        Coverage percentage (0.0 to 1.0)
    """
    if document_area <= 0:
        return 0.0
    
    total_detection_area = sum(d.area for d in detections)
    return min(1.0, total_detection_area / document_area)