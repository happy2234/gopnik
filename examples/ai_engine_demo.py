#!/usr/bin/env python3
"""
Demonstration of Gopnik AI Engine Components.

This script demonstrates the usage of the Computer Vision, NLP, and Hybrid AI engines
for PII detection in documents.
"""

import sys
import os
import numpy as np
from pathlib import Path

# Add the src directory to the path so we can import gopnik modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gopnik.ai import ComputerVisionEngine, NLPEngine, HybridAIEngine
from gopnik.models.pii import PIIType


def demo_cv_engine():
    """Demonstrate Computer Vision engine functionality."""
    print("=" * 60)
    print("COMPUTER VISION ENGINE DEMO")
    print("=" * 60)
    
    # Create CV engine with configuration
    config = {
        'face_detection': {
            'enabled': True,
            'confidence_threshold': 0.7
        },
        'signature_detection': {
            'enabled': True,
            'confidence_threshold': 0.6
        },
        'barcode_detection': {
            'enabled': True,
            'confidence_threshold': 0.8
        }
    }
    
    cv_engine = ComputerVisionEngine(config)
    
    print(f"CV Engine initialized: {cv_engine.is_initialized}")
    print(f"Supported PII types: {cv_engine.get_supported_types()}")
    
    # Create a mock image for demonstration
    test_image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
    
    print("\nProcessing test image...")
    detections = cv_engine.detect_pii(test_image)
    
    print(f"Found {len(detections)} visual PII detections:")
    for i, detection in enumerate(detections, 1):
        print(f"  {i}. {detection.type.value} - Confidence: {detection.confidence:.2f}")
        print(f"     Location: ({detection.bounding_box.x1}, {detection.bounding_box.y1}) to "
              f"({detection.bounding_box.x2}, {detection.bounding_box.y2})")
        print(f"     Area: {detection.area} pixels")
    
    # Get model information
    model_info = cv_engine.get_model_info()
    print(f"\nModel Information:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")


def demo_nlp_engine():
    """Demonstrate NLP engine functionality."""
    print("\n" + "=" * 60)
    print("NLP ENGINE DEMO")
    print("=" * 60)
    
    # Create NLP engine with configuration
    config = {
        'email_detection': {'enabled': True, 'confidence_threshold': 0.9},
        'phone_detection': {'enabled': True, 'confidence_threshold': 0.8},
        'name_detection': {'enabled': True, 'confidence_threshold': 0.7},
        'id_detection': {'enabled': True, 'confidence_threshold': 0.8},
        'financial_detection': {'enabled': True, 'confidence_threshold': 0.9},
        'multilingual': {'enabled': True, 'indic_scripts': True}
    }
    
    nlp_engine = NLPEngine(config)
    
    print(f"NLP Engine initialized: {nlp_engine.is_initialized}")
    print(f"Supported PII types: {nlp_engine.get_supported_types()}")
    
    # Test document with various PII types
    test_document = """
    CONFIDENTIAL EMPLOYEE RECORD
    
    Name: Dr. Rajesh Kumar Sharma
    Employee ID: EMP-2024-001
    Email: rajesh.sharma@techcorp.com
    Phone: +91-9876543210
    Alternate Phone: (555) 123-4567
    
    Personal Information:
    Date of Birth: 15/03/1985
    SSN: 123-45-6789
    Address: 42 MG Road, Bangalore, Karnataka 560001
    
    Financial Details:
    Credit Card: 4111-1111-1111-1111
    Bank Account: 1234567890123456
    
    Emergency Contact:
    Name: Priya Sharma
    Phone: +91-9876543211
    Email: priya.sharma@gmail.com
    
    IP Address for VPN: 192.168.1.100
    
    Hindi Name: राजेश कुमार शर्मा
    """
    
    print("\nProcessing test document...")
    detections = nlp_engine.detect_pii(test_document)
    
    print(f"Found {len(detections)} text PII detections:")
    
    # Group detections by type
    by_type = {}
    for detection in detections:
        pii_type = detection.type.value
        if pii_type not in by_type:
            by_type[pii_type] = []
        by_type[pii_type].append(detection)
    
    for pii_type, type_detections in by_type.items():
        print(f"\n  {pii_type.upper()} ({len(type_detections)} found):")
        for detection in type_detections:
            print(f"    - '{detection.text_content}' (confidence: {detection.confidence:.2f})")
            if 'pattern_name' in detection.metadata:
                print(f"      Pattern: {detection.metadata['pattern_name']}")
    
    # Get model information
    model_info = nlp_engine.get_model_info()
    print(f"\nModel Information:")
    for key, value in model_info.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for subkey, subvalue in value.items():
                print(f"    {subkey}: {subvalue}")
        else:
            print(f"  {key}: {value}")


def demo_hybrid_engine():
    """Demonstrate Hybrid AI engine functionality."""
    print("\n" + "=" * 60)
    print("HYBRID AI ENGINE DEMO")
    print("=" * 60)
    
    # Create hybrid engine with both CV and NLP
    config = {
        'cv_engine': {
            'enabled': True,
            'config': {
                'face_detection': {'enabled': True, 'confidence_threshold': 0.6},
                'signature_detection': {'enabled': True, 'confidence_threshold': 0.5}
            }
        },
        'nlp_engine': {
            'enabled': True,
            'config': {
                'email_detection': {'enabled': True},
                'phone_detection': {'enabled': True},
                'name_detection': {'enabled': True}
            }
        },
        'detection_merging': {
            'enabled': True,
            'iou_threshold': 0.5,
            'confidence_boost': 0.1
        },
        'cross_validation': {
            'enabled': True,
            'text_visual_correlation': True
        },
        'filtering': {
            'min_confidence': 0.5,
            'enable_ranking': True
        }
    }
    
    hybrid_engine = HybridAIEngine(config)
    
    print(f"Hybrid Engine initialized: {hybrid_engine.is_initialized}")
    print(f"Supported PII types: {hybrid_engine.get_supported_types()}")
    
    # Test with structured document data
    test_image = np.random.randint(0, 255, (300, 500, 3), dtype=np.uint8)
    test_text = """
    John Smith
    Senior Developer
    john.smith@example.com
    Phone: (555) 987-6543
    Employee ID: EMP-12345
    """
    
    document_data = {
        'image_data': test_image,
        'text_data': test_text
    }
    
    print("\nProcessing hybrid document (image + text)...")
    detections = hybrid_engine.detect_pii(document_data)
    
    print(f"Found {len(detections)} total PII detections after hybrid processing:")
    
    for i, detection in enumerate(detections, 1):
        print(f"\n  {i}. {detection.type.value}")
        print(f"     Confidence: {detection.confidence:.2f}")
        print(f"     Method: {detection.detection_method}")
        
        if detection.text_content:
            print(f"     Content: '{detection.text_content}'")
        
        # Show hybrid processing metadata
        metadata = detection.metadata
        if 'engine' in metadata:
            print(f"     Engine: {metadata['engine']}")
        if 'cross_validated' in metadata:
            print(f"     Cross-validated: {metadata['cross_validated']}")
        if 'hybrid_merged' in metadata:
            print(f"     Hybrid merged: {metadata['hybrid_merged']}")
        if 'ranking_score' in metadata:
            print(f"     Ranking score: {metadata['ranking_score']:.2f}")
    
    # Get detection statistics
    stats = hybrid_engine.get_detection_statistics(detections)
    print(f"\nDetection Statistics:")
    print(f"  Total detections: {stats['total_detections']}")
    print(f"  By engine: {stats['by_engine']}")
    print(f"  By type: {stats['by_type']}")
    print(f"  Cross-validated: {stats['cross_validated_count']}")
    print(f"  Merged detections: {stats['merged_count']}")
    
    confidence_stats = stats['confidence_stats']
    if stats['total_detections'] > 0:
        print(f"  Confidence range: {confidence_stats['min']:.2f} - {confidence_stats['max']:.2f}")
        print(f"  Average confidence: {confidence_stats['mean']:.2f}")
        print(f"  High confidence (≥0.8): {confidence_stats['high_confidence_count']}")
    else:
        print("  No detections found for confidence analysis")


def demo_multilingual_support():
    """Demonstrate multilingual PII detection."""
    print("\n" + "=" * 60)
    print("MULTILINGUAL SUPPORT DEMO")
    print("=" * 60)
    
    # Create NLP engine with multilingual support
    config = {
        'name_detection': {'enabled': True, 'confidence_threshold': 0.6},
        'email_detection': {'enabled': True},
        'phone_detection': {'enabled': True, 'formats': ['indian', 'us', 'international']},
        'multilingual': {
            'enabled': True,
            'languages': ['en', 'hi', 'bn', 'ta'],
            'indic_scripts': True
        }
    }
    
    nlp_engine = NLPEngine(config)
    
    # Test documents in different languages
    test_documents = {
        'English': """
        Name: John Smith
        Email: john@example.com
        Phone: +1-555-123-4567
        """,
        
        'Hindi (Devanagari)': """
        नाम: राम शर्मा
        ईमेल: ram.sharma@example.com
        फोन: +91-9876543210
        """,
        
        'Mixed Language': """
        Name: Priya Patel / प्रिया पटेल
        Email: priya.patel@techcorp.in
        Mobile: +91-9876543210
        Office: (022) 2345-6789
        """
    }
    
    for language, document in test_documents.items():
        print(f"\n{language} Document:")
        print("-" * 40)
        
        detections = nlp_engine.detect_pii(document)
        
        print(f"Found {len(detections)} PII detections:")
        for detection in detections:
            print(f"  - {detection.type.value}: '{detection.text_content}' "
                  f"(confidence: {detection.confidence:.2f})")
            
            if 'script' in detection.metadata:
                print(f"    Script: {detection.metadata['script']}")


def main():
    """Run all demonstrations."""
    print("GOPNIK AI ENGINE DEMONSTRATION")
    print("This demo shows the capabilities of the AI engines for PII detection.")
    print("Note: This uses mock implementations for demonstration purposes.")
    
    try:
        # Run individual engine demos
        demo_cv_engine()
        demo_nlp_engine()
        demo_hybrid_engine()
        demo_multilingual_support()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("✓ Computer Vision PII detection (faces, signatures, barcodes)")
        print("✓ NLP text PII detection (emails, phones, names, IDs, etc.)")
        print("✓ Hybrid engine combining CV and NLP results")
        print("✓ Detection merging and deduplication")
        print("✓ Cross-validation between engines")
        print("✓ Confidence-based filtering and ranking")
        print("✓ Multilingual support including Indic scripts")
        print("✓ Comprehensive detection statistics")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())