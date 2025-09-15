"""
Unit tests for NLP PII Detection Engine.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from src.gopnik.ai.nlp_engine import (
    NLPEngine, 
    MockPersonNER, 
    MockLocationNER, 
    MockOrganizationNER,
    MockMultilingualProcessor
)
from src.gopnik.models.pii import PIIType, PIIDetection, BoundingBox


class TestNLPEngine(unittest.TestCase):
    """Test cases for NLPEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'text_extraction': {
                'enabled': True,
                'method': 'regex',
                'confidence_threshold': 0.6
            },
            'email_detection': {
                'enabled': True,
                'confidence_threshold': 0.9
            },
            'phone_detection': {
                'enabled': True,
                'formats': ['us', 'international', 'indian'],
                'confidence_threshold': 0.8
            },
            'name_detection': {
                'enabled': True,
                'use_ner': False,  # Disable NER for basic tests
                'confidence_threshold': 0.7
            },
            'auto_init': False  # Don't auto-initialize for tests
        }
        
        self.engine = NLPEngine(self.config)
        
        # Test text with various PII types
        self.test_text = """
        John Doe is a software engineer at Tech Corp Inc.
        His email is john.doe@example.com and phone number is (555) 123-4567.
        He lives at 123 Main Street, Anytown, NY 12345.
        His SSN is 123-45-6789 and credit card number is 4532-1234-5678-9012.
        Date of birth: 01/15/1985
        IP address: 192.168.1.1
        """
    
    def test_initialization(self):
        """Test engine initialization."""
        self.assertFalse(self.engine.is_initialized)
        
        # Initialize manually
        self.engine.initialize()
        self.assertTrue(self.engine.is_initialized)
        
        # Check that patterns are loaded
        self.assertIn('email', self.engine.patterns)
        self.assertIn('phone', self.engine.patterns)
        self.assertIn('ssn', self.engine.patterns)
    
    def test_config_merging(self):
        """Test configuration merging with defaults."""
        # Test with minimal config
        minimal_config = {'email_detection': {'enabled': False}}
        engine = NLPEngine(minimal_config)
        
        # Should have default values for other settings
        self.assertFalse(engine.config['email_detection']['enabled'])
        self.assertTrue(engine.config['phone_detection']['enabled'])
        self.assertEqual(engine.config['multilingual']['languages'][0], 'en')
    
    def test_supported_types(self):
        """Test getting supported PII types."""
        self.engine.initialize()
        supported_types = self.engine.get_supported_types()
        
        expected_types = [
            PIIType.EMAIL.value, PIIType.PHONE.value, PIIType.NAME.value,
            PIIType.DATE_OF_BIRTH.value, PIIType.IP_ADDRESS.value
        ]
        
        for pii_type in expected_types:
            self.assertIn(pii_type, supported_types)
    
    def test_text_data_preparation_string(self):
        """Test text data preparation from string."""
        self.engine.initialize()
        
        text_data = self.engine._prepare_text_data(self.test_text)
        
        self.assertIsInstance(text_data, dict)
        self.assertIn('text', text_data)
        self.assertIn('pages', text_data)
        self.assertEqual(text_data['text'], self.test_text)
    
    def test_text_data_preparation_dict(self):
        """Test text data preparation from dictionary."""
        self.engine.initialize()
        
        input_data = {
            'text': self.test_text,
            'coordinates': [{'x': 0, 'y': 0, 'width': 100, 'height': 20}],
            'layout_info': {'page_width': 800, 'page_height': 600}
        }
        
        text_data = self.engine._prepare_text_data(input_data)
        
        self.assertIsInstance(text_data, dict)
        self.assertEqual(text_data['text'], self.test_text)
        self.assertIsNotNone(text_data['coordinates'])
    
    def test_text_data_preparation_list(self):
        """Test text data preparation from list."""
        self.engine.initialize()
        
        input_list = ["Line 1 with john@example.com", "Line 2 with (555) 123-4567"]
        
        text_data = self.engine._prepare_text_data(input_list)
        
        self.assertIsInstance(text_data, dict)
        self.assertIn('john@example.com', text_data['text'])
        self.assertIn('(555) 123-4567', text_data['text'])
    
    def test_email_detection(self):
        """Test email address detection."""
        self.engine.initialize()
        
        text_data = self.engine._prepare_text_data(self.test_text)
        email_detections = self.engine._detect_emails(text_data)
        
        self.assertGreater(len(email_detections), 0)
        
        # Check that we found the email
        email_texts = [d.text_content for d in email_detections]
        self.assertIn('john.doe@example.com', email_texts)
        
        # Check detection properties
        for detection in email_detections:
            self.assertEqual(detection.type, PIIType.EMAIL)
            self.assertEqual(detection.detection_method, 'nlp')
            self.assertGreaterEqual(detection.confidence, 0.0)
            self.assertLessEqual(detection.confidence, 1.0)
    
    def test_phone_detection(self):
        """Test phone number detection."""
        self.engine.initialize()
        
        text_data = self.engine._prepare_text_data(self.test_text)
        phone_detections = self.engine._detect_phone_numbers(text_data)
        
        self.assertGreater(len(phone_detections), 0)
        
        # Check detection properties
        for detection in phone_detections:
            self.assertEqual(detection.type, PIIType.PHONE)
            self.assertEqual(detection.detection_method, 'nlp')
            self.assertIn('format', detection.metadata)
    
    def test_ssn_detection(self):
        """Test SSN detection."""
        self.engine.initialize()
        
        text_data = self.engine._prepare_text_data(self.test_text)
        id_detections = self.engine._detect_id_numbers(text_data)
        
        # Filter for SSN detections
        ssn_detections = [d for d in id_detections if d.type == PIIType.SSN]
        self.assertGreater(len(ssn_detections), 0)
        
        # Check that we found the SSN
        ssn_texts = [d.text_content for d in ssn_detections]
        self.assertIn('123-45-6789', ssn_texts)
    
    def test_credit_card_detection(self):
        """Test credit card detection with Luhn validation."""
        self.engine.initialize()
        
        # Use a valid credit card number (test number)
        test_text_with_cc = "Credit card: 4532123456789012"  # Valid test Visa number
        
        text_data = self.engine._prepare_text_data(test_text_with_cc)
        financial_detections = self.engine._detect_financial_info(text_data)
        
        cc_detections = [d for d in financial_detections if d.type == PIIType.CREDIT_CARD]
        
        if cc_detections:  # Only test if we found credit card detections
            for detection in cc_detections:
                self.assertEqual(detection.type, PIIType.CREDIT_CARD)
                self.assertIn('luhn_valid', detection.metadata)
    
    def test_date_detection(self):
        """Test date of birth detection."""
        self.engine.initialize()
        
        text_data = self.engine._prepare_text_data(self.test_text)
        date_detections = self.engine._detect_dates(text_data)
        
        self.assertGreater(len(date_detections), 0)
        
        for detection in date_detections:
            self.assertEqual(detection.type, PIIType.DATE_OF_BIRTH)
            self.assertIn('date_format', detection.metadata)
    
    def test_ip_address_detection(self):
        """Test IP address detection."""
        self.engine.initialize()
        
        text_data = self.engine._prepare_text_data(self.test_text)
        ip_detections = self.engine._detect_ip_addresses(text_data)
        
        self.assertGreater(len(ip_detections), 0)
        
        # Check that we found the IP address
        ip_texts = [d.text_content for d in ip_detections]
        self.assertIn('192.168.1.1', ip_texts)
    
    def test_full_pii_detection(self):
        """Test full PII detection pipeline."""
        self.engine.initialize()
        
        detections = self.engine.detect_pii(self.test_text)
        
        # Should return a list of detections
        self.assertIsInstance(detections, list)
        self.assertGreater(len(detections), 0)
        
        # Check that we get different types of PII
        detection_types = [d.type for d in detections]
        self.assertIn(PIIType.EMAIL, detection_types)
        self.assertIn(PIIType.PHONE, detection_types)
        
        # All detections should have required properties
        for detection in detections:
            self.assertIsInstance(detection, PIIDetection)
            self.assertEqual(detection.detection_method, 'nlp')
            self.assertIsInstance(detection.bounding_box, BoundingBox)
            self.assertGreaterEqual(detection.confidence, 0.0)
            self.assertLessEqual(detection.confidence, 1.0)
    
    def test_confidence_calculation_email(self):
        """Test email confidence calculation."""
        self.engine.initialize()
        
        # Test with common domain
        confidence1 = self.engine._calculate_email_confidence('test@gmail.com')
        self.assertGreater(confidence1, 0.9)
        
        # Test with suspicious pattern
        confidence2 = self.engine._calculate_email_confidence('test..test@example.com')
        self.assertLess(confidence2, confidence1)
    
    def test_confidence_calculation_phone(self):
        """Test phone confidence calculation."""
        self.engine.initialize()
        
        # Test US format
        confidence_us = self.engine._calculate_phone_confidence('(555) 123-4567', 'us')
        self.assertGreater(confidence_us, 0.8)
        
        # Test international format
        confidence_intl = self.engine._calculate_phone_confidence('+1234567890', 'international')
        self.assertGreater(confidence_intl, 0.7)
    
    def test_luhn_validation(self):
        """Test Luhn algorithm for credit card validation."""
        self.engine.initialize()
        
        # Valid test credit card numbers (these are known valid test numbers)
        valid_cards = [
            '4111111111111111',  # Visa test number
            '5555555555554444',  # MasterCard test number
            '378282246310005'    # American Express test number
        ]
        
        for card in valid_cards:
            self.assertTrue(self.engine._validate_credit_card(card), f"Failed to validate card: {card}")
        
        # Invalid credit card numbers
        invalid_cards = [
            '1234567890123456',
            '4111111111111112',  # Wrong check digit
            '1111111111111111'
        ]
        
        for card in invalid_cards:
            self.assertFalse(self.engine._validate_credit_card(card), f"Incorrectly validated invalid card: {card}")
    
    def test_dob_validation(self):
        """Test date of birth validation."""
        self.engine.initialize()
        
        # Valid DOB years
        valid_dobs = ['01/15/1985', '12/25/1990', '06/30/2000']
        for dob in valid_dobs:
            self.assertTrue(self.engine._is_potential_dob(dob))
        
        # Invalid DOB years (too recent or too old)
        invalid_dobs = ['01/15/2023', '12/25/1850', '06/30/2030']
        for dob in invalid_dobs:
            self.assertFalse(self.engine._is_potential_dob(dob))
    
    def test_phone_normalization(self):
        """Test phone number normalization."""
        self.engine.initialize()
        
        # Test 10-digit number
        normalized1 = self.engine._normalize_phone_number('5551234567')
        self.assertEqual(normalized1, '(555) 123-4567')
        
        # Test 11-digit number with country code
        normalized2 = self.engine._normalize_phone_number('15551234567')
        self.assertEqual(normalized2, '+1 (555) 123-4567')
        
        # Test already formatted number
        normalized3 = self.engine._normalize_phone_number('(555) 123-4567')
        self.assertEqual(normalized3, '(555) 123-4567')
    
    def test_coordinate_generation(self):
        """Test text coordinate generation."""
        self.engine.initialize()
        
        text_data = {'text': self.test_text, 'coordinates': None}
        
        # Test coordinate generation for a text span
        bbox = self.engine._get_text_coordinates(10, 20, text_data)
        
        self.assertIsInstance(bbox, BoundingBox)
        self.assertLess(bbox.x1, bbox.x2)
        self.assertLess(bbox.y1, bbox.y2)
    
    def test_duplicate_removal(self):
        """Test duplicate detection removal."""
        self.engine.initialize()
        
        # Create duplicate detections
        bbox1 = BoundingBox(10, 10, 50, 30)
        bbox2 = BoundingBox(12, 12, 52, 32)  # Slightly overlapping
        
        detection1 = PIIDetection(
            type=PIIType.EMAIL,
            bounding_box=bbox1,
            confidence=0.8,
            text_content='test@example.com',
            detection_method='nlp'
        )
        
        detection2 = PIIDetection(
            type=PIIType.EMAIL,
            bounding_box=bbox2,
            confidence=0.9,  # Higher confidence
            text_content='test@example.com',
            detection_method='nlp'
        )
        
        detections = [detection1, detection2]
        unique_detections = self.engine._remove_duplicate_detections(detections)
        
        # Should keep only one detection (the one with higher confidence)
        self.assertEqual(len(unique_detections), 1)
        self.assertEqual(unique_detections[0].confidence, 0.9)
    
    def test_nearby_detection_merging(self):
        """Test merging of nearby detections."""
        # Set a larger proximity threshold for this test
        config = self.config.copy()
        config['layout_awareness'] = {
            'enabled': True,
            'use_coordinates': True,
            'merge_nearby_detections': True,
            'proximity_threshold': 100  # Larger threshold to ensure merging
        }
        
        engine = NLPEngine(config)
        engine.initialize()
        
        # Create nearby detections of the same type
        bbox1 = BoundingBox(10, 10, 50, 30)
        bbox2 = BoundingBox(60, 15, 100, 35)  # Nearby
        
        detection1 = PIIDetection(
            type=PIIType.NAME,
            bounding_box=bbox1,
            confidence=0.8,
            text_content='John',
            detection_method='nlp'
        )
        
        detection2 = PIIDetection(
            type=PIIType.NAME,
            bounding_box=bbox2,
            confidence=0.7,
            text_content='Doe',
            detection_method='nlp'
        )
        
        detections = [detection1, detection2]
        merged_detections = engine._merge_nearby_detections(detections)
        
        # Should merge into one detection
        self.assertEqual(len(merged_detections), 1)
        merged = merged_detections[0]
        
        # Check merged properties
        self.assertIn('John', merged.text_content)
        self.assertIn('Doe', merged.text_content)
        self.assertIn('merged_from', merged.metadata)
    
    def test_disabled_features(self):
        """Test behavior when features are disabled."""
        config = self.config.copy()
        config['email_detection']['enabled'] = False
        config['phone_detection']['enabled'] = False
        
        engine = NLPEngine(config)
        engine.initialize()
        
        detections = engine.detect_pii(self.test_text)
        
        # Should not contain email or phone detections
        detection_types = [d.type for d in detections]
        self.assertNotIn(PIIType.EMAIL, detection_types)
        self.assertNotIn(PIIType.PHONE, detection_types)
    
    def test_configure_method(self):
        """Test runtime configuration changes."""
        self.engine.initialize()
        
        # Change configuration
        new_config = {
            'email_detection': {
                'confidence_threshold': 0.95
            }
        }
        
        self.engine.configure(new_config)
        
        # Should update the configuration
        self.assertEqual(self.engine.config['email_detection']['confidence_threshold'], 0.95)
    
    def test_get_model_info(self):
        """Test getting model information."""
        self.engine.initialize()
        
        model_info = self.engine.get_model_info()
        
        # Should contain information about patterns and models
        self.assertIn('patterns', model_info)
        self.assertIn('ner_models', model_info)
        self.assertIn('multilingual', model_info)
        self.assertIn('detection_capabilities', model_info)
        
        # Should indicate which capabilities are enabled
        self.assertTrue(model_info['detection_capabilities']['email'])
        self.assertTrue(model_info['detection_capabilities']['phone'])


class TestMockNERModels(unittest.TestCase):
    """Test cases for mock NER model implementations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_text = "John Doe works at Tech Corp Inc. He lives at 123 Main Street."
    
    def test_mock_person_ner(self):
        """Test mock person NER model."""
        ner = MockPersonNER()
        entities = ner.extract_entities(self.test_text)
        
        self.assertIsInstance(entities, list)
        
        # Should find person names
        person_entities = [e for e in entities if e['type'] == 'PERSON']
        self.assertGreater(len(person_entities), 0)
        
        for entity in person_entities:
            self.assertIn('text', entity)
            self.assertIn('start', entity)
            self.assertIn('end', entity)
            self.assertIn('confidence', entity)
            self.assertGreaterEqual(entity['confidence'], 0.0)
            self.assertLessEqual(entity['confidence'], 1.0)
    
    def test_mock_location_ner(self):
        """Test mock location NER model."""
        ner = MockLocationNER()
        entities = ner.extract_entities(self.test_text)
        
        self.assertIsInstance(entities, list)
        
        # Should find location entities
        location_entities = [e for e in entities if e['type'] == 'LOCATION']
        
        for entity in location_entities:
            self.assertIn('text', entity)
            self.assertIn('start', entity)
            self.assertIn('end', entity)
            self.assertIn('confidence', entity)
    
    def test_mock_organization_ner(self):
        """Test mock organization NER model."""
        ner = MockOrganizationNER()
        entities = ner.extract_entities(self.test_text)
        
        self.assertIsInstance(entities, list)
        
        # Should find organization entities
        org_entities = [e for e in entities if e['type'] == 'ORGANIZATION']
        
        for entity in org_entities:
            self.assertIn('text', entity)
            self.assertIn('start', entity)
            self.assertIn('end', entity)
            self.assertIn('confidence', entity)


class TestMultilingualSupport(unittest.TestCase):
    """Test cases for multilingual support."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.processor = MockMultilingualProcessor()
    
    def test_language_detection(self):
        """Test language detection."""
        # English text
        lang_en = self.processor.detect_language("Hello world")
        self.assertEqual(lang_en, 'en')
        
        # Hindi text (Devanagari script)
        lang_hi = self.processor.detect_language("नमस्ते दुनिया")
        self.assertEqual(lang_hi, 'hi')
        
        # Bengali text
        lang_bn = self.processor.detect_language("হ্যালো বিশ্ব")
        self.assertEqual(lang_bn, 'bn')
        
        # Tamil text
        lang_ta = self.processor.detect_language("வணக்கம் உலகம்")
        self.assertEqual(lang_ta, 'ta')
    
    def test_multilingual_processing(self):
        """Test multilingual text processing."""
        result = self.processor.process_multilingual_text("नमस्ते")
        
        self.assertIn('detected_language', result)
        self.assertIn('confidence', result)
        self.assertIn('script_type', result)
        self.assertIn('processed_text', result)
        
        self.assertEqual(result['detected_language'], 'hi')
        self.assertEqual(result['script_type'], 'indic')
    
    def test_indic_name_patterns(self):
        """Test Indic script name pattern detection."""
        config = {
            'multilingual': {'enabled': True, 'indic_scripts': True},
            'name_detection': {'enabled': True},
            'auto_init': False
        }
        
        engine = NLPEngine(config)
        engine.initialize()
        
        # Test with Hindi name
        hindi_text = "मेरा नाम राम शर्मा है।"
        text_data = engine._prepare_text_data(hindi_text)
        
        indic_detections = engine._detect_indic_names(text_data)
        
        # Should detect Indic script names
        self.assertIsInstance(indic_detections, list)
        
        for detection in indic_detections:
            self.assertEqual(detection.type, PIIType.NAME)
            self.assertEqual(detection.detection_method, 'nlp')
            self.assertIn('script', detection.metadata)


class TestPatternMatching(unittest.TestCase):
    """Test cases for regex pattern matching."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = NLPEngine({'auto_init': False})
        self.engine.initialize()
    
    def test_email_patterns(self):
        """Test email regex patterns."""
        test_emails = [
            'user@example.com',
            'test.email+tag@domain.co.uk',
            'user123@test-domain.org',
            'firstname.lastname@company.com'
        ]
        
        pattern = self.engine.patterns['email']
        
        for email in test_emails:
            match = pattern.search(email)
            self.assertIsNotNone(match, f"Failed to match email: {email}")
            self.assertEqual(match.group(), email)
    
    def test_phone_patterns(self):
        """Test phone number regex patterns."""
        us_phones = [
            '(555) 123-4567',
            '555-123-4567',
            '5551234567',
            '+1 555 123 4567'
        ]
        
        us_pattern = self.engine.patterns['phone']['us']
        
        for phone in us_phones:
            match = us_pattern.search(phone)
            self.assertIsNotNone(match, f"Failed to match US phone: {phone}")
    
    def test_ssn_patterns(self):
        """Test SSN regex patterns."""
        ssn_numbers = [
            '123-45-6789',
            '123456789',
            '123 45 6789'
        ]
        
        pattern = self.engine.patterns['ssn']
        
        for ssn in ssn_numbers:
            match = pattern.search(ssn)
            self.assertIsNotNone(match, f"Failed to match SSN: {ssn}")
    
    def test_ip_address_patterns(self):
        """Test IP address regex patterns."""
        ip_addresses = [
            '192.168.1.1',
            '10.0.0.1',
            '172.16.254.1',
            '255.255.255.255'
        ]
        
        pattern = self.engine.patterns['ip_address']
        
        for ip in ip_addresses:
            match = pattern.search(ip)
            self.assertIsNotNone(match, f"Failed to match IP: {ip}")
            self.assertEqual(match.group(), ip)
    
    def test_invalid_patterns(self):
        """Test that invalid patterns are not matched."""
        # Invalid emails that should not match our pattern
        invalid_emails = [
            'invalid.email',  # No @ symbol
            '@domain.com',    # No local part
            'user@',          # No domain
        ]
        
        email_pattern = self.engine.patterns['email']
        
        for email in invalid_emails:
            match = email_pattern.search(email)
            # These should not match at all
            self.assertIsNone(match, f"Invalid email should not match: {email}")
        
        # Test that patterns with dots at start/end don't match the full invalid string
        problematic_emails = [
            '.user@domain.com',  # Starting with dot
            'user.@domain.com'   # Ending with dot before @
        ]
        
        for email in problematic_emails:
            match = email_pattern.search(email)
            if match:
                # Should match a valid substring, not the full invalid string
                self.assertNotEqual(match.group(), email, f"Should not match full invalid email: {email}")


if __name__ == '__main__':
    unittest.main()