"""
PII detection data models and types.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Optional, Dict, Any


class PIIType(Enum):
    """Enumeration of supported PII types."""
    FACE = "face"
    SIGNATURE = "signature"
    BARCODE = "barcode"
    QR_CODE = "qr_code"
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    SSN = "ssn"
    ID_NUMBER = "id_number"
    CREDIT_CARD = "credit_card"
    DATE_OF_BIRTH = "date_of_birth"


@dataclass
class PIIDetection:
    """
    Represents a detected PII element in a document.
    
    Attributes:
        type: Type of PII detected
        coordinates: Bounding box coordinates (x1, y1, x2, y2)
        confidence: Detection confidence score (0.0 to 1.0)
        text_content: Actual text content if applicable
        metadata: Additional detection metadata
    """
    type: PIIType
    coordinates: Tuple[int, int, int, int]
    confidence: float
    text_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate detection data after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        
        x1, y1, x2, y2 = self.coordinates
        if x1 >= x2 or y1 >= y2:
            raise ValueError(f"Invalid coordinates: {self.coordinates}")
        
        if any(coord < 0 for coord in self.coordinates):
            raise ValueError(f"Coordinates cannot be negative: {self.coordinates}")
    
    @property
    def width(self) -> int:
        """Get width of detection bounding box."""
        return self.coordinates[2] - self.coordinates[0]
    
    @property
    def height(self) -> int:
        """Get height of detection bounding box."""
        return self.coordinates[3] - self.coordinates[1]
    
    @property
    def area(self) -> int:
        """Get area of detection bounding box."""
        return self.width * self.height
    
    def overlaps_with(self, other: 'PIIDetection', threshold: float = 0.5) -> bool:
        """
        Check if this detection overlaps with another detection.
        
        Args:
            other: Another PII detection
            threshold: Minimum overlap ratio to consider as overlap
            
        Returns:
            True if detections overlap above threshold
        """
        x1_max = max(self.coordinates[0], other.coordinates[0])
        y1_max = max(self.coordinates[1], other.coordinates[1])
        x2_min = min(self.coordinates[2], other.coordinates[2])
        y2_min = min(self.coordinates[3], other.coordinates[3])
        
        if x1_max >= x2_min or y1_max >= y2_min:
            return False
        
        overlap_area = (x2_min - x1_max) * (y2_min - y1_max)
        union_area = self.area + other.area - overlap_area
        
        return (overlap_area / union_area) >= threshold if union_area > 0 else False