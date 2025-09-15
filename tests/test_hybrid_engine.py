"""
Unit tests for Hybrid AI PII Detection Engine.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from src.gopnik.ai.hybrid_engine import HybridAIEngine
from src.gopnik.ai.cv_engine import ComputerVisionEngine
from src.gopnik.ai.nlp_engine import NLPEngine
from src.gopnik.models.pii import PIIType, PIIDetection, BoundingBox, PIIDetectionCollection


class TestHybridAIEngine(unittest.TestCase):
    """Test cases for HybridAIEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'cv_engine': {
                'enabled': True,
                'config': {'auto_init': False}
            },
            'nlp_engine': {
                'enabled': True,
                'config': {'auto_init': False}
            },
            'detection_merging': {
                'enabled': True,
                'iou_threshold': 0.5,
                'confidence_boost': 0.1
            },
            'filtering': {
                'min_confidence': 0.5,
                'max_detections_per_type': 10
            },
            'auto_init': False  # Don't auto-initialize for tests
        }
        
        self.engine = HybridAIEngine(self.config)
        
        # Create mock detections for testing
        self.cv_detection = PIIDetection(
            type=PIIType.FACE,
            bounding_box=BoundingBox(10, 10, 50, 50),
            confidence=0.8,
            detection_method='cv',
            metadata={'engine': 'cv'}
        )
        
        self.nlp_detection = PIIDetection(
            type=PIIType.NAME,
            bounding_box=BoundingBox(15, 15, 55, 55),
            confidence=0.7,
            text_content='John Doe',
            detection_method='nlp',
            metadata={'engine': 'nlp'}
        )
        
        self.overlapping_detection = PIIDetection(
            type=PIIType.FACE,
            bounding_box=BoundingBox(12, 12, 52, 52),
            confidence=0.9,
            detection_method='cv',
            metadata={'engine': 'cv'}
        )
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertFalse(self.engine.is_initialized)
        
        # Mock the sub-engines to avoid actual initialization
        with patch.object(self.engine, '_initialize_cv_engine') as mock_cv, \
             patch.object(self.engine, '_initialize_nlp_engine') as mock_nlp:
            
            # Mock that at least one engine gets initialized
            def mock_cv_init():
                self.engine.cv_engine = Mock()
            
            mock_cv.side_effect = mock_cv_init
            
            self.engine.initialize()
            
            self.assertTrue(self.engine.is_initialized)
            mock_cv.assert_called_once()
            mock_nlp.assert_called_once()
    
    def test_config_merging(self):
        """Test configuration merging with defaults."""
        # Test with minimal config
        minimal_config = {'cv_engine': {'enabled': False}}
        engine = HybridAIEngine(minimal_config)
        
        # Should have default values for other settings
        self.assertFalse(engine.config['cv_engine']['enabled'])
        self.assertTrue(engine.config['nlp_engine']['enabled'])
        self.assertTrue(engine.config['detection_merging']['enabled'])
    
    def test_document_data_preparation(self):
        """Test document data preparation for both engines."""
        # Test with structured data
        structured_data = {
            'image_data': 'mock_image',
            'text_data': 'mock_text'
        }
        
        cv_data, nlp_data = self.engine._prepare_document_data(structured_data)
        self.assertEqual(cv_data, 'mock_image')
        self.assertEqual(nlp_data, 'mock_text')
        
        # Test with simple string
        text_data = "Simple text string"
        cv_data, nlp_data = self.engine._prepare_document_data(text_data)
        self.assertIsNone(cv_data)
        self.assertEqual(nlp_data, text_data)
        
        # Test with file path
        file_path = "/path/to/document.pdf"
        cv_data, nlp_data = self.engine._prepare_document_data(file_path)
        self.assertEqual(cv_data, file_path)
        self.assertEqual(nlp_data, file_path)
    
    def test_detection_correlation(self):
        """Test detection correlation between engines."""
        # Test compatible types
        self.assertTrue(self.engine._are_compatible_types(PIIType.FACE, PIIType.NAME))
        self.assertTrue(self.engine._are_compatible_types(PIIType.SIGNATURE, PIIType.NAME))
        self.assertFalse(self.engine._are_compatible_types(PIIType.FACE, PIIType.EMAIL))
        
        # Test same types
        self.assertTrue(self.engine._are_compatible_types(PIIType.EMAIL, PIIType.EMAIL))
    
    def test_text_content_correlation(self):
        """Test text content correlation."""
        # Exact match
        self.assertTrue(self.engine._text_contents_correlate("John Doe", "John Doe"))
        
        # Case insensitive
        self.assertTrue(self.engine._text_contents_correlate("John Doe", "john doe"))
        
        # Substring match
        self.assertTrue(self.engine._text_contents_correlate("John", "John Doe"))
        
        # No correlation
        self.assertFalse(self.engine._text_contents_correlate("John", "Jane"))
        
        # Empty strings
        self.assertFalse(self.engine._text_contents_correlate("", "John"))
        self.assertFalse(self.engine._text_contents_correlate("John", ""))
    
    def test_detection_merging(self):
        """Test detection merging functionality."""
        # Create overlapping detections
        detections = [self.cv_detection, self.overlapping_detection]
        
        merged_detections = self.engine._merge_detections(detections)
        
        # Should merge into one detection
        self.assertEqual(len(merged_detections), 1)
        
        merged = merged_detections[0]
        self.assertEqual(merged.detection_method, 'hybrid')
        self.assertIn('merged_from', merged.metadata)
        self.assertIn('hybrid_merged', merged.metadata)
        self.assertTrue(merged.metadata['hybrid_merged'])
    
    def test_detection_merging_no_overlap(self):
        """Test detection merging with non-overlapping detections."""
        # Create non-overlapping detections
        detection1 = PIIDetection(
            type=PIIType.EMAIL,
            bounding_box=BoundingBox(10, 10, 50, 30),
            confidence=0.8,
            text_content='test@example.com',
            detection_method='nlp',
            metadata={'engine': 'nlp'}
        )
        
        detection2 = PIIDetection(
            type=PIIType.PHONE,
            bounding_box=BoundingBox(100, 100, 150, 120),
            confidence=0.9,
            text_content='555-1234',
            detection_method='nlp',
            metadata={'engine': 'nlp'}
        )
        
        detections = [detection1, detection2]
        merged_detections = self.engine._merge_detections(detections)
        
        # Should not merge (different types and no overlap)
        self.assertEqual(len(merged_detections), 2)
    
    def test_detection_filtering(self):
        """Test detection filtering by confidence."""
        # Create detections with different confidence levels
        high_conf_detection = PIIDetection(
            type=PIIType.EMAIL,
            bounding_box=BoundingBox(10, 10, 50, 30),
            confidence=0.9,
            detection_method='nlp'
        )
        
        low_conf_detection = PIIDetection(
            type=PIIType.PHONE,
            bounding_box=BoundingBox(60, 60, 100, 80),
            confidence=0.3,  # Below threshold
            detection_method='nlp'
        )
        
        detections = [high_conf_detection, low_conf_detection]
        filtered_detections = self.engine._filter_detections(detections)
        
        # Should filter out low confidence detection
        self.assertEqual(len(filtered_detections), 1)
        self.assertEqual(filtered_detections[0].confidence, 0.9)
    
    def test_detection_limiting_per_type(self):
        """Test limiting detections per type."""
        # Create multiple detections of the same type
        detections = []
        for i in range(15):  # More than max_per_type (10)
            detection = PIIDetection(
                type=PIIType.EMAIL,
                bounding_box=BoundingBox(i*10, i*10, i*10+40, i*10+20),
                confidence=0.8 + (i * 0.01),  # Varying confidence
                detection_method='nlp'
            )
            detections.append(detection)
        
        limited_detections = self.engine._limit_detections_per_type(detections, 10)
        
        # Should limit to 10 detections
        self.assertEqual(len(limited_detections), 10)
        
        # Should keep the highest confidence detections
        confidences = [d.confidence for d in limited_detections]
        self.assertAlmostEqual(max(confidences), 0.94, places=2)  # Highest confidence should be kept
    
    def test_ranking_score_calculation(self):
        """Test ranking score calculation."""
        # Test basic detection
        basic_detection = PIIDetection(
            type=PIIType.EMAIL,
            bounding_box=BoundingBox(10, 10, 50, 30),
            confidence=0.8,
            detection_method='nlp'
        )
        
        basic_score = self.engine._calculate_ranking_score(basic_detection)
        self.assertGreaterEqual(basic_score, 0.8)
        
        # Test sensitive PII detection
        sensitive_detection = PIIDetection(
            type=PIIType.SSN,
            bounding_box=BoundingBox(10, 10, 50, 30),
            confidence=0.8,
            detection_method='nlp'
        )
        
        sensitive_score = self.engine._calculate_ranking_score(sensitive_detection)
        self.assertGreater(sensitive_score, basic_score)
        
        # Test cross-validated detection
        cv_detection = PIIDetection(
            type=PIIType.NAME,
            bounding_box=BoundingBox(10, 10, 50, 30),
            confidence=0.8,
            detection_method='hybrid',
            metadata={'cross_validated': True}
        )
        
        cv_score = self.engine._calculate_ranking_score(cv_detection)
        self.assertGreater(cv_score, basic_score)
    
    def test_detection_ranking(self):
        """Test detection ranking functionality."""
        # Create detections with different characteristics
        detections = [
            PIIDetection(
                type=PIIType.EMAIL,
                bounding_box=BoundingBox(10, 10, 50, 30),
                confidence=0.7,
                detection_method='nlp'
            ),
            PIIDetection(
                type=PIIType.SSN,  # Sensitive type
                bounding_box=BoundingBox(60, 60, 100, 80),
                confidence=0.6,
                detection_method='nlp'
            ),
            PIIDetection(
                type=PIIType.NAME,
                bounding_box=BoundingBox(110, 110, 150, 130),
                confidence=0.8,
                detection_method='hybrid',
                metadata={'cross_validated': True}
            )
        ]
        
        ranked_detections = self.engine._rank_detections(detections)
        
        # Should have ranking scores
        for detection in ranked_detections:
            self.assertIn('ranking_score', detection.metadata)
        
        # Should be sorted by ranking score (highest first)
        scores = [d.metadata['ranking_score'] for d in ranked_detections]
        self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_cross_validation(self):
        """Test cross-validation between engines."""
        # Create compatible detections from different engines
        cv_detection = PIIDetection(
            type=PIIType.FACE,
            bounding_box=BoundingBox(10, 10, 50, 50),
            confidence=0.7,
            detection_method='cv',
            metadata={'engine': 'cv'}
        )
        
        nlp_detection = PIIDetection(
            type=PIIType.NAME,
            bounding_box=BoundingBox(15, 15, 55, 55),  # Overlapping
            confidence=0.6,
            text_content='John Doe',
            detection_method='nlp',
            metadata={'engine': 'nlp'}
        )
        
        detections = [cv_detection, nlp_detection]
        cross_validated = self.engine._cross_validate_detections(detections)
        
        # Should boost confidence for correlated detections
        cv_det = next(d for d in cross_validated if d.metadata.get('engine') == 'cv')
        nlp_det = next(d for d in cross_validated if d.metadata.get('engine') == 'nlp')
        
        # Confidence should be boosted if cross-validation found correlation
        # (This depends on the specific implementation and overlap)
        self.assertGreaterEqual(cv_det.confidence, 0.7)
        self.assertGreaterEqual(nlp_det.confidence, 0.6)
    
    def test_supported_types(self):
        """Test getting supported PII types."""
        # Mock sub-engines
        mock_cv_engine = Mock()
        mock_cv_engine.get_supported_types.return_value = ['face', 'signature']
        
        mock_nlp_engine = Mock()
        mock_nlp_engine.get_supported_types.return_value = ['email', 'phone', 'name']
        
        self.engine.cv_engine = mock_cv_engine
        self.engine.nlp_engine = mock_nlp_engine
        
        supported_types = self.engine.get_supported_types()
        
        # Should combine types from both engines
        expected_types = {'face', 'signature', 'email', 'phone', 'name'}
        self.assertEqual(set(supported_types), expected_types)
    
    def test_configure_method(self):
        """Test runtime configuration changes."""
        # Mock sub-engines
        mock_cv_engine = Mock()
        mock_nlp_engine = Mock()
        
        self.engine.cv_engine = mock_cv_engine
        self.engine.nlp_engine = mock_nlp_engine
        self.engine.is_initialized = True
        
        # Change configuration
        new_config = {
            'detection_merging': {
                'iou_threshold': 0.7
            },
            'cv_engine': {
                'config': {'face_detection': {'confidence_threshold': 0.9}}
            }
        }
        
        self.engine.configure(new_config)
        
        # Should update the configuration
        self.assertEqual(self.engine.config['detection_merging']['iou_threshold'], 0.7)
        
        # Should configure sub-engines
        mock_cv_engine.configure.assert_called_once()
    
    def test_get_model_info(self):
        """Test getting model information."""
        # Mock sub-engines
        mock_cv_engine = Mock()
        mock_cv_engine.get_model_info.return_value = {'cv': 'info'}
        
        mock_nlp_engine = Mock()
        mock_nlp_engine.get_model_info.return_value = {'nlp': 'info'}
        
        self.engine.cv_engine = mock_cv_engine
        self.engine.nlp_engine = mock_nlp_engine
        self.engine.is_initialized = True
        
        model_info = self.engine.get_model_info()
        
        # Should contain hybrid engine info
        self.assertIn('hybrid_engine', model_info)
        self.assertTrue(model_info['hybrid_engine']['initialized'])
        
        # Should contain sub-engine info
        self.assertIn('cv_engine', model_info)
        self.assertIn('nlp_engine', model_info)
    
    def test_detection_statistics(self):
        """Test detection statistics calculation."""
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
            ),
            PIIDetection(
                type=PIIType.NAME,
                bounding_box=BoundingBox(110, 110, 150, 130),
                confidence=0.7,
                detection_method='hybrid',
                metadata={'hybrid_merged': True}
            )
        ]
        
        stats = self.engine.get_detection_statistics(detections)
        
        # Should have basic statistics
        self.assertEqual(stats['total_detections'], 3)
        self.assertIn('by_engine', stats)
        self.assertIn('by_type', stats)
        self.assertIn('confidence_stats', stats)
        
        # Should count special cases
        self.assertEqual(stats['cross_validated_count'], 1)
        self.assertEqual(stats['merged_count'], 1)
        self.assertEqual(stats['hybrid_processed_count'], 1)
        
        # Should have confidence statistics
        self.assertEqual(stats['confidence_stats']['min'], 0.7)
        self.assertEqual(stats['confidence_stats']['max'], 0.9)
        self.assertAlmostEqual(stats['confidence_stats']['mean'], 0.8, places=1)
    
    def test_full_detection_pipeline_mock(self):
        """Test full detection pipeline with mocked engines."""
        # Mock sub-engines
        mock_cv_engine = Mock()
        mock_cv_engine.detect_pii.return_value = [self.cv_detection]
        
        mock_nlp_engine = Mock()
        mock_nlp_engine.detect_pii.return_value = [self.nlp_detection]
        
        self.engine.cv_engine = mock_cv_engine
        self.engine.nlp_engine = mock_nlp_engine
        self.engine.is_initialized = True
        
        # Run detection
        document_data = {'image_data': 'mock_image', 'text_data': 'mock_text'}
        detections = self.engine.detect_pii(document_data)
        
        # Should return processed detections
        self.assertIsInstance(detections, list)
        self.assertGreater(len(detections), 0)
        
        # Should call both engines
        mock_cv_engine.detect_pii.assert_called_once_with('mock_image')
        mock_nlp_engine.detect_pii.assert_called_once_with('mock_text')
    
    def test_engine_failure_handling(self):
        """Test handling of engine failures."""
        # Mock engines with one failing
        mock_cv_engine = Mock()
        mock_cv_engine.detect_pii.side_effect = Exception("CV engine failed")
        
        mock_nlp_engine = Mock()
        mock_nlp_engine.detect_pii.return_value = [self.nlp_detection]
        
        self.engine.cv_engine = mock_cv_engine
        self.engine.nlp_engine = mock_nlp_engine
        self.engine.is_initialized = True
        
        # Should still work with one engine failing
        detections = self.engine.detect_pii("test document")
        
        # Should return NLP detections only
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].metadata['engine'], 'nlp')
    
    def test_empty_detection_handling(self):
        """Test handling of empty detection results."""
        # Mock engines returning empty results
        mock_cv_engine = Mock()
        mock_cv_engine.detect_pii.return_value = []
        
        mock_nlp_engine = Mock()
        mock_nlp_engine.detect_pii.return_value = []
        
        self.engine.cv_engine = mock_cv_engine
        self.engine.nlp_engine = mock_nlp_engine
        self.engine.is_initialized = True
        
        # Should handle empty results gracefully
        detections = self.engine.detect_pii("test document")
        
        self.assertEqual(len(detections), 0)
        self.assertIsInstance(detections, list)
    
    def test_single_engine_mode(self):
        """Test operation with only one engine enabled."""
        # Test with only NLP engine
        config = self.config.copy()
        config['cv_engine']['enabled'] = False
        
        engine = HybridAIEngine(config)
        
        # Mock NLP engine
        mock_nlp_engine = Mock()
        mock_nlp_engine.detect_pii.return_value = [self.nlp_detection]
        
        engine.nlp_engine = mock_nlp_engine
        engine.cv_engine = None
        engine.is_initialized = True
        
        detections = engine.detect_pii("test document")
        
        # Should work with single engine
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].metadata['engine'], 'nlp')


if __name__ == '__main__':
    unittest.main()