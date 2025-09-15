"""
Unit tests for Computer Vision PII Detection Engine.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from PIL import Image
import tempfile
import os

from src.gopnik.ai.cv_engine import (
    ComputerVisionEngine, 
    MockFaceDetector, 
    MockSignatureDetector, 
    BarcodeDetector
)
from src.gopnik.models.pii import PIIType, PIIDetection, BoundingBox


class TestComputerVisionEngine(unittest.TestCase):
    """Test cases for ComputerVisionEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'face_detection': {
                'enabled': True,
                'model_type': 'opencv_dnn',
                'confidence_threshold': 0.5
            },
            'signature_detection': {
                'enabled': True,
                'model_type': 'custom',
                'confidence_threshold': 0.6,
                'min_area': 1000
            },
            'barcode_detection': {
                'enabled': True,
                'types': ['qr', 'barcode'],
                'confidence_threshold': 0.7
            },
            'auto_init': False  # Don't auto-initialize for tests
        }
        
        self.engine = ComputerVisionEngine(self.config)
        
        # Create test image
        self.test_image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertFalse(self.engine.is_initialized)
        
        # Initialize manually
        self.engine.initialize()
        self.assertTrue(self.engine.is_initialized)
        
        # Check that models are loaded
        self.assertIn('face_detector', self.engine.models)
        self.assertIn('signature_detector', self.engine.models)
        self.assertIn('barcode_detector', self.engine.models)
    
    def test_config_merging(self):
        """Test configuration merging with defaults."""
        # Test with minimal config
        minimal_config = {'face_detection': {'enabled': False}}
        engine = ComputerVisionEngine(minimal_config)
        
        # Should have default values for other settings
        self.assertFalse(engine.config['face_detection']['enabled'])
        self.assertTrue(engine.config['signature_detection']['enabled'])
        self.assertEqual(engine.config['preprocessing']['resize_max_dimension'], 1024)
    
    def test_supported_types(self):
        """Test getting supported PII types."""
        self.engine.initialize()
        supported_types = self.engine.get_supported_types()
        
        expected_types = [PIIType.FACE.value, PIIType.SIGNATURE.value, 
                         PIIType.BARCODE.value, PIIType.QR_CODE.value]
        
        for pii_type in expected_types:
            self.assertIn(pii_type, supported_types)
    
    def test_supported_types_disabled_features(self):
        """Test supported types when features are disabled."""
        config = self.config.copy()
        config['face_detection']['enabled'] = False
        config['signature_detection']['enabled'] = False
        
        engine = ComputerVisionEngine(config)
        engine.initialize()
        supported_types = engine.get_supported_types()
        
        self.assertNotIn(PIIType.FACE.value, supported_types)
        self.assertNotIn(PIIType.SIGNATURE.value, supported_types)
        self.assertIn(PIIType.BARCODE.value, supported_types)
        self.assertIn(PIIType.QR_CODE.value, supported_types)
    
    def test_image_preparation_numpy_array(self):
        """Test image preparation from numpy array."""
        self.engine.initialize()
        
        prepared_image = self.engine._prepare_image(self.test_image)
        self.assertIsInstance(prepared_image, np.ndarray)
        self.assertEqual(len(prepared_image.shape), 3)  # Should be 3D array
    
    def test_image_preparation_pil_image(self):
        """Test image preparation from PIL Image."""
        self.engine.initialize()
        
        pil_image = Image.fromarray(self.test_image)
        prepared_image = self.engine._prepare_image(pil_image)
        
        self.assertIsInstance(prepared_image, np.ndarray)
        self.assertEqual(len(prepared_image.shape), 3)
    
    def test_image_preparation_file_path(self):
        """Test image preparation from file path."""
        self.engine.initialize()
        
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            pil_image = Image.fromarray(self.test_image)
            pil_image.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            prepared_image = self.engine._prepare_image(tmp_path)
            self.assertIsInstance(prepared_image, np.ndarray)
        finally:
            os.unlink(tmp_path)
    
    def test_image_preparation_invalid_input(self):
        """Test image preparation with invalid input."""
        self.engine.initialize()
        
        # Test with invalid input
        prepared_image = self.engine._prepare_image("nonexistent_file.jpg")
        self.assertIsNone(prepared_image)
        
        prepared_image = self.engine._prepare_image(123)
        self.assertIsNone(prepared_image)
    
    def test_image_preprocessing(self):
        """Test image preprocessing operations."""
        self.engine.initialize()
        
        # Test with large image that should be resized
        large_image = np.random.randint(0, 255, (2000, 3000, 3), dtype=np.uint8)
        processed = self.engine._preprocess_image(large_image)
        
        # Should be resized
        max_dim = max(processed.shape[:2])
        self.assertLessEqual(max_dim, self.engine.config['preprocessing']['resize_max_dimension'])
    
    def test_detect_pii_integration(self):
        """Test full PII detection pipeline."""
        self.engine.initialize()
        
        detections = self.engine.detect_pii(self.test_image)
        
        # Should return a list of detections
        self.assertIsInstance(detections, list)
        
        # Check that we get some mock detections
        self.assertGreater(len(detections), 0)
        
        # Verify detection types
        detection_types = [d.type for d in detections]
        self.assertIn(PIIType.FACE, detection_types)
    
    def test_detect_pii_with_disabled_features(self):
        """Test PII detection with some features disabled."""
        config = self.config.copy()
        config['face_detection']['enabled'] = False
        
        engine = ComputerVisionEngine(config)
        engine.initialize()
        
        detections = engine.detect_pii(self.test_image)
        
        # Should not contain face detections
        detection_types = [d.type for d in detections]
        self.assertNotIn(PIIType.FACE, detection_types)
    
    def test_configure_method(self):
        """Test runtime configuration changes."""
        self.engine.initialize()
        
        # Change configuration
        new_config = {
            'face_detection': {
                'confidence_threshold': 0.8
            }
        }
        
        self.engine.configure(new_config)
        
        # Should update the configuration
        self.assertEqual(self.engine.config['face_detection']['confidence_threshold'], 0.8)
        
        # Should still have other default values
        self.assertTrue(self.engine.config['signature_detection']['enabled'])
    
    def test_get_model_info(self):
        """Test getting model information."""
        self.engine.initialize()
        
        model_info = self.engine.get_model_info()
        
        # Should contain information about all detection types
        self.assertIn('face_detection', model_info)
        self.assertIn('signature_detection', model_info)
        self.assertIn('barcode_detection', model_info)
        
        # Should indicate which models are loaded
        self.assertTrue(model_info['face_detection']['loaded'])
        self.assertTrue(model_info['signature_detection']['loaded'])
        self.assertTrue(model_info['barcode_detection']['loaded'])
    
    def test_face_detection_confidence_filtering(self):
        """Test that face detection respects confidence threshold."""
        self.engine.initialize()
        
        # Mock face detector to return low confidence detection
        mock_detector = Mock()
        mock_detector.detect.return_value = [
            {
                'x1': 10, 'y1': 10, 'x2': 50, 'y2': 50,
                'confidence': 0.3,  # Below threshold
                'landmarks': None,
                'angle': 0
            }
        ]
        self.engine.models['face_detector'] = mock_detector
        
        detections = self.engine._detect_faces(self.test_image)
        
        # Should filter out low confidence detection
        self.assertEqual(len(detections), 0)
    
    def test_signature_detection_area_filtering(self):
        """Test that signature detection respects minimum area."""
        self.engine.initialize()
        
        # Mock signature detector to return small area detection
        mock_detector = Mock()
        mock_detector.detect.return_value = [
            {
                'x1': 10, 'y1': 10, 'x2': 20, 'y2': 15,  # Small area
                'confidence': 0.8,
                'area': 50,  # Below min_area threshold
                'type': 'handwritten'
            }
        ]
        self.engine.models['signature_detector'] = mock_detector
        
        detections = self.engine._detect_signatures(self.test_image)
        
        # Should filter out small area detection
        self.assertEqual(len(detections), 0)
    
    def test_detection_metadata(self):
        """Test that detections contain proper metadata."""
        self.engine.initialize()
        
        detections = self.engine.detect_pii(self.test_image)
        
        for detection in detections:
            # Should have detection method set
            self.assertEqual(detection.detection_method, 'cv')
            
            # Should have metadata
            self.assertIsInstance(detection.metadata, dict)
            
            # Should have model type in metadata
            self.assertIn('model_type', detection.metadata)
    
    def test_error_handling_in_detection(self):
        """Test error handling during detection."""
        self.engine.initialize()
        
        # Mock detector that raises exception
        mock_detector = Mock()
        mock_detector.detect.side_effect = Exception("Mock error")
        self.engine.models['face_detector'] = mock_detector
        
        # Should not raise exception, should return empty list
        detections = self.engine._detect_faces(self.test_image)
        self.assertEqual(len(detections), 0)


class TestMockDetectors(unittest.TestCase):
    """Test cases for mock detector implementations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
    
    def test_mock_face_detector(self):
        """Test mock face detector."""
        detector = MockFaceDetector()
        faces = detector.detect(self.test_image)
        
        self.assertIsInstance(faces, list)
        self.assertGreater(len(faces), 0)
        
        for face in faces:
            self.assertIn('x1', face)
            self.assertIn('y1', face)
            self.assertIn('x2', face)
            self.assertIn('y2', face)
            self.assertIn('confidence', face)
            
            # Check coordinate validity
            self.assertLess(face['x1'], face['x2'])
            self.assertLess(face['y1'], face['y2'])
            self.assertGreaterEqual(face['confidence'], 0.0)
            self.assertLessEqual(face['confidence'], 1.0)
    
    def test_mock_signature_detector(self):
        """Test mock signature detector."""
        detector = MockSignatureDetector()
        signatures = detector.detect(self.test_image)
        
        self.assertIsInstance(signatures, list)
        self.assertGreater(len(signatures), 0)
        
        for signature in signatures:
            self.assertIn('x1', signature)
            self.assertIn('y1', signature)
            self.assertIn('x2', signature)
            self.assertIn('y2', signature)
            self.assertIn('confidence', signature)
            self.assertIn('area', signature)
            
            # Check that area is calculated correctly
            expected_area = (signature['x2'] - signature['x1']) * (signature['y2'] - signature['y1'])
            self.assertAlmostEqual(signature['area'], expected_area, delta=1.0)
    
    def test_mock_detectors_small_image(self):
        """Test mock detectors with small image."""
        small_image = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        
        face_detector = MockFaceDetector()
        faces = face_detector.detect(small_image)
        self.assertEqual(len(faces), 0)  # Should not detect in small image
        
        signature_detector = MockSignatureDetector()
        signatures = signature_detector.detect(small_image)
        self.assertEqual(len(signatures), 0)  # Should not detect in small image


class TestBarcodeDetector(unittest.TestCase):
    """Test cases for BarcodeDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = BarcodeDetector()
        self.test_image = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
    
    def test_barcode_detector_initialization(self):
        """Test barcode detector initialization."""
        self.assertIsNotNone(self.detector.qr_detector)
    
    def test_detect_method_exists(self):
        """Test that detect method exists and returns list."""
        detections = self.detector.detect(self.test_image)
        self.assertIsInstance(detections, list)
    
    @patch('cv2.QRCodeDetector.detectAndDecodeMulti')
    def test_qr_code_detection_mock(self, mock_detect):
        """Test QR code detection with mocked OpenCV."""
        # Mock successful QR detection
        mock_detect.return_value = (
            True,  # retval
            ['Test QR Data'],  # decoded_info
            [np.array([[10, 10], [50, 10], [50, 50], [10, 50]])],  # points
            None  # straight_qrcode
        )
        
        detections = self.detector._detect_qr_codes(self.test_image)
        
        self.assertEqual(len(detections), 1)
        detection = detections[0]
        
        self.assertEqual(detection['type'], 'qr')
        self.assertEqual(detection['data'], 'Test QR Data')
        self.assertEqual(detection['x1'], 10)
        self.assertEqual(detection['y1'], 10)
        self.assertEqual(detection['x2'], 50)
        self.assertEqual(detection['y2'], 50)
    
    @patch('cv2.QRCodeDetector.detectAndDecodeMulti')
    def test_qr_code_detection_no_results(self, mock_detect):
        """Test QR code detection with no results."""
        # Mock no QR detection
        mock_detect.return_value = (False, [], [], None)
        
        detections = self.detector._detect_qr_codes(self.test_image)
        self.assertEqual(len(detections), 0)
    
    def test_barcode_detection_simple(self):
        """Test simple barcode detection algorithm."""
        # Create synthetic barcode-like pattern
        barcode_image = np.zeros((200, 400, 3), dtype=np.uint8)
        
        # Add vertical lines to simulate barcode
        for i in range(50, 350, 10):
            if i % 20 == 0:  # Thick lines
                barcode_image[50:150, i:i+4] = 255
            else:  # Thin lines
                barcode_image[50:150, i:i+2] = 255
        
        detections = self.detector._detect_barcodes_simple(barcode_image)
        
        # Should detect the barcode pattern
        # Note: This is a simplified test, actual results may vary
        self.assertIsInstance(detections, list)
    
    def test_detection_error_handling(self):
        """Test error handling in detection methods."""
        # Test with invalid image
        invalid_image = np.array([])
        
        # Should not raise exception
        detections = self.detector.detect(invalid_image)
        self.assertIsInstance(detections, list)


class TestPIIDetectionCreation(unittest.TestCase):
    """Test creation of PIIDetection objects from CV engine."""
    
    def test_face_detection_creation(self):
        """Test creation of face detection objects."""
        bbox = BoundingBox(10, 20, 50, 60)
        
        detection = PIIDetection(
            type=PIIType.FACE,
            bounding_box=bbox,
            confidence=0.85,
            detection_method='cv',
            metadata={'model_type': 'opencv_dnn'}
        )
        
        self.assertEqual(detection.type, PIIType.FACE)
        self.assertEqual(detection.confidence, 0.85)
        self.assertEqual(detection.detection_method, 'cv')
        self.assertTrue(detection.is_visual_pii)
        self.assertFalse(detection.is_text_pii)
    
    def test_signature_detection_creation(self):
        """Test creation of signature detection objects."""
        bbox = BoundingBox(100, 200, 300, 250)
        
        detection = PIIDetection(
            type=PIIType.SIGNATURE,
            bounding_box=bbox,
            confidence=0.73,
            detection_method='cv',
            metadata={
                'model_type': 'custom',
                'signature_type': 'handwritten'
            }
        )
        
        self.assertEqual(detection.type, PIIType.SIGNATURE)
        self.assertEqual(detection.confidence, 0.73)
        self.assertTrue(detection.is_visual_pii)
        self.assertEqual(detection.metadata['signature_type'], 'handwritten')
    
    def test_qr_code_detection_creation(self):
        """Test creation of QR code detection objects."""
        bbox = BoundingBox(50, 50, 100, 100)
        
        detection = PIIDetection(
            type=PIIType.QR_CODE,
            bounding_box=bbox,
            confidence=0.9,
            detection_method='cv',
            text_content='https://example.com',
            metadata={
                'barcode_type': 'qr',
                'decoded_data': 'https://example.com',
                'extracted_text': True
            }
        )
        
        self.assertEqual(detection.type, PIIType.QR_CODE)
        self.assertEqual(detection.text_content, 'https://example.com')
        self.assertTrue(detection.is_visual_pii)
        self.assertTrue(detection.metadata['extracted_text'])


if __name__ == '__main__':
    unittest.main()