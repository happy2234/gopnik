"""
Integration tests for AI engine components.
"""

import unittest
import numpy as np
from PIL import Image

from src.gopnik.ai import ComputerVisionEngine, NLPEngine, HybridAIEngine
from src.gopnik.models.pii import PIIType


class TestAIEngineIntegration(unittest.TestCase):
    """Integration tests for AI engine components."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Sample document with both visual and text PII
        self.test_text = """
        John Doe
        Software Engineer
        Email: john.doe@company.com
        Phone: (555) 123-4567
        SSN: 123-45-6789
        Address: 123 Main Street, Anytown, NY 12345
        """
        
        # Create a simple test image
        self.test_image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
    
    def test_cv_engine_standalone(self):
        """Test CV engine standalone functionality."""
        config = {
            'face_detection': {'enabled': True, 'confidence_threshold': 0.5},
            'signature_detection': {'enabled': True, 'confidence_threshold': 0.6},
            'barcode_detection': {'enabled': True, 'confidence_threshold': 0.7}
        }
        
        cv_engine = ComputerVisionEngine(config)
        detections = cv_engine.detect_pii(self.test_image)
        
        # Should return detections (mock implementations will generate some)
        self.assertIsInstance(detections, list)
        
        # Check that all detections are visual PII types
        for detection in detections:
            self.assertTrue(detection.is_visual_pii)
            self.assertEqual(detection.detection_method, 'cv')
    
    def test_nlp_engine_standalone(self):
        """Test NLP engine standalone functionality."""
        config = {
            'email_detection': {'enabled': True},
            'phone_detection': {'enabled': True},
            'name_detection': {'enabled': True},
            'id_detection': {'enabled': True}
        }
        
        nlp_engine = NLPEngine(config)
        detections = nlp_engine.detect_pii(self.test_text)
        
        # Should detect multiple PII types
        self.assertGreater(len(detections), 0)
        
        # Check detection types
        detection_types = [d.type for d in detections]
        self.assertIn(PIIType.EMAIL, detection_types)
        self.assertIn(PIIType.PHONE, detection_types)
        
        # Check that all detections are text PII types or general types
        for detection in detections:
            self.assertEqual(detection.detection_method, 'nlp')
    
    def test_hybrid_engine_integration(self):
        """Test hybrid engine with both CV and NLP."""
        config = {
            'cv_engine': {
                'enabled': True,
                'config': {
                    'face_detection': {'enabled': True},
                    'signature_detection': {'enabled': True}
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
            'detection_merging': {'enabled': True},
            'cross_validation': {'enabled': True}
        }
        
        hybrid_engine = HybridAIEngine(config)
        
        # Test with structured document data
        document_data = {
            'image_data': self.test_image,
            'text_data': self.test_text
        }
        
        detections = hybrid_engine.detect_pii(document_data)
        
        # Should get detections from both engines
        self.assertIsInstance(detections, list)
        
        if detections:  # Only test if we got detections
            # Check that we have hybrid processing metadata
            engines_used = set()
            for detection in detections:
                if 'engine' in detection.metadata:
                    engines_used.add(detection.metadata['engine'])
            
            # Should have used at least one engine
            self.assertGreater(len(engines_used), 0)
    
    def test_hybrid_engine_text_only(self):
        """Test hybrid engine with text-only input."""
        config = {
            'cv_engine': {'enabled': True, 'config': {}},
            'nlp_engine': {'enabled': True, 'config': {}},
            'detection_merging': {'enabled': True}
        }
        
        hybrid_engine = HybridAIEngine(config)
        detections = hybrid_engine.detect_pii(self.test_text)
        
        # Should work with text-only input
        self.assertIsInstance(detections, list)
        
        # Should primarily use NLP engine for text
        if detections:
            nlp_detections = [d for d in detections if d.metadata.get('engine') == 'nlp']
            self.assertGreater(len(nlp_detections), 0)
    
    def test_hybrid_engine_image_only(self):
        """Test hybrid engine with image-only input."""
        config = {
            'cv_engine': {'enabled': True, 'config': {}},
            'nlp_engine': {'enabled': True, 'config': {}},
            'detection_merging': {'enabled': True}
        }
        
        hybrid_engine = HybridAIEngine(config)
        detections = hybrid_engine.detect_pii(self.test_image)
        
        # Should work with image-only input
        self.assertIsInstance(detections, list)
        
        # Should primarily use CV engine for images
        if detections:
            cv_detections = [d for d in detections if d.metadata.get('engine') == 'cv']
            self.assertGreater(len(cv_detections), 0)
    
    def test_engine_configuration_consistency(self):
        """Test that engine configurations are consistent."""
        # Test CV engine supported types
        cv_engine = ComputerVisionEngine()
        cv_types = cv_engine.get_supported_types()
        
        # Should include visual PII types
        self.assertIn(PIIType.FACE.value, cv_types)
        self.assertIn(PIIType.SIGNATURE.value, cv_types)
        
        # Test NLP engine supported types
        nlp_engine = NLPEngine()
        nlp_types = nlp_engine.get_supported_types()
        
        # Should include text PII types
        self.assertIn(PIIType.EMAIL.value, nlp_types)
        self.assertIn(PIIType.PHONE.value, nlp_types)
        self.assertIn(PIIType.NAME.value, nlp_types)
        
        # Test hybrid engine supported types
        hybrid_engine = HybridAIEngine()
        hybrid_types = hybrid_engine.get_supported_types()
        
        # Should include types from both engines
        for pii_type in cv_types:
            self.assertIn(pii_type, hybrid_types)
        
        for pii_type in nlp_types:
            self.assertIn(pii_type, hybrid_types)
    
    def test_detection_statistics(self):
        """Test detection statistics functionality."""
        hybrid_engine = HybridAIEngine()
        
        # Create mock detections
        from src.gopnik.models.pii import PIIDetection, BoundingBox
        
        detections = [
            PIIDetection(
                type=PIIType.EMAIL,
                bounding_box=BoundingBox(10, 10, 50, 30),
                confidence=0.9,
                detection_method='nlp',
                metadata={'engine': 'nlp', 'hybrid_processing': True}
            ),
            PIIDetection(
                type=PIIType.FACE,
                bounding_box=BoundingBox(60, 60, 100, 100),
                confidence=0.8,
                detection_method='cv',
                metadata={'engine': 'cv', 'cross_validated': True}
            )
        ]
        
        stats = hybrid_engine.get_detection_statistics(detections)
        
        # Should have comprehensive statistics
        self.assertEqual(stats['total_detections'], 2)
        self.assertIn('by_engine', stats)
        self.assertIn('by_type', stats)
        self.assertIn('confidence_stats', stats)
        
        # Check engine distribution
        self.assertEqual(stats['by_engine']['nlp'], 1)
        self.assertEqual(stats['by_engine']['cv'], 1)
        
        # Check type distribution
        self.assertEqual(stats['by_type']['email'], 1)
        self.assertEqual(stats['by_type']['face'], 1)
    
    def test_error_handling(self):
        """Test error handling in AI engines."""
        # Test with invalid input
        cv_engine = ComputerVisionEngine()
        detections = cv_engine.detect_pii(None)
        self.assertEqual(len(detections), 0)
        
        nlp_engine = NLPEngine()
        detections = nlp_engine.detect_pii(None)
        self.assertEqual(len(detections), 0)
        
        hybrid_engine = HybridAIEngine()
        detections = hybrid_engine.detect_pii(None)
        self.assertEqual(len(detections), 0)
    
    def test_model_info_consistency(self):
        """Test that model info is consistent across engines."""
        cv_engine = ComputerVisionEngine()
        cv_info = cv_engine.get_model_info()
        
        nlp_engine = NLPEngine()
        nlp_info = nlp_engine.get_model_info()
        
        hybrid_engine = HybridAIEngine()
        hybrid_info = hybrid_engine.get_model_info()
        
        # All should return dictionaries with relevant information
        self.assertIsInstance(cv_info, dict)
        self.assertIsInstance(nlp_info, dict)
        self.assertIsInstance(hybrid_info, dict)
        
        # Hybrid engine should include sub-engine info
        self.assertIn('hybrid_engine', hybrid_info)
        if hybrid_engine.cv_engine:
            self.assertIn('cv_engine', hybrid_info)
        if hybrid_engine.nlp_engine:
            self.assertIn('nlp_engine', hybrid_info)


if __name__ == '__main__':
    unittest.main()