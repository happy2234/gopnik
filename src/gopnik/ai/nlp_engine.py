"""
Natural Language Processing PII Detection Engine.

Implements layout-aware NLP for text PII detection including names, emails,
phone numbers, addresses, IDs, and multilingual text processing.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Union, Tuple, Pattern
from pathlib import Path
import json

from ..core.interfaces import AIEngineInterface
from ..models.pii import PIIDetection, PIIType, BoundingBox


logger = logging.getLogger(__name__)


class NLPEngine(AIEngineInterface):
    """
    Natural Language Processing engine for detecting text-based PII elements.
    
    Supports detection of:
    - Names (person names, organization names)
    - Email addresses
    - Phone numbers (various formats)
    - Addresses (street addresses, postal codes)
    - ID numbers (SSN, passport, driver license, etc.)
    - Credit card numbers
    - Dates of birth
    - Medical record numbers
    - Bank account numbers
    - IP addresses
    
    Features:
    - Layout-aware processing using coordinate information
    - Multilingual support including Indic scripts
    - Configurable regex patterns and NER models
    - Context-aware validation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the NLP engine.
        
        Args:
            config: Configuration dictionary for the engine
        """
        self.config = config or {}
        self.models = {}
        self.patterns = {}
        self.is_initialized = False
        
        # Default configuration
        self.default_config = {
            'text_extraction': {
                'enabled': True,
                'method': 'regex',  # or 'ner', 'hybrid'
                'confidence_threshold': 0.6
            },
            'name_detection': {
                'enabled': True,
                'use_ner': True,
                'min_length': 2,
                'max_length': 50,
                'confidence_threshold': 0.7
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
            'address_detection': {
                'enabled': True,
                'use_ner': True,
                'confidence_threshold': 0.7
            },
            'id_detection': {
                'enabled': True,
                'types': ['ssn', 'passport', 'driver_license', 'national_id'],
                'confidence_threshold': 0.8
            },
            'financial_detection': {
                'enabled': True,
                'types': ['credit_card', 'bank_account', 'routing_number'],
                'confidence_threshold': 0.9
            },
            'medical_detection': {
                'enabled': True,
                'confidence_threshold': 0.8
            },
            'multilingual': {
                'enabled': True,
                'languages': ['en', 'hi', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'or', 'pa'],
                'indic_scripts': True
            },
            'layout_awareness': {
                'enabled': True,
                'use_coordinates': True,
                'merge_nearby_detections': True,
                'proximity_threshold': 50
            }
        }
        
        # Merge with provided config
        self._merge_config()
        
        # Initialize patterns and models if auto_init is enabled
        if self.config.get('auto_init', True):
            self.initialize()
    
    def _merge_config(self):
        """Merge provided config with defaults."""
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if subkey not in self.config[key]:
                        self.config[key][subkey] = subvalue
    
    def initialize(self) -> None:
        """Initialize the NLP models and regex patterns."""
        try:
            logger.info("Initializing NLP PII Detection Engine")
            
            # Initialize regex patterns
            self._initialize_patterns()
            
            # Initialize NER models if enabled
            if self._is_ner_enabled():
                self._initialize_ner_models()
            
            # Initialize multilingual support
            if self.config['multilingual']['enabled']:
                self._initialize_multilingual_support()
            
            self.is_initialized = True
            logger.info("NLP Engine initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize NLP engine: {e}")
            raise
    
    def _is_ner_enabled(self) -> bool:
        """Check if any NER-based detection is enabled."""
        return (self.config['name_detection'].get('use_ner', False) or
                self.config['address_detection'].get('use_ner', False))
    
    def _initialize_patterns(self) -> None:
        """Initialize regex patterns for PII detection."""
        logger.info("Initializing regex patterns")
        
        # Email patterns (more restrictive to avoid invalid patterns)
        self.patterns['email'] = re.compile(
            r'\b[A-Za-z0-9](?:[A-Za-z0-9._+%-]*[A-Za-z0-9])?@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}\b',
            re.IGNORECASE
        )
        
        # Phone number patterns
        phone_patterns = {
            'us': re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
            'international': re.compile(r'\+(?:[0-9] ?){6,14}[0-9]'),
            'indian': re.compile(r'\b(?:\+91[-.\s]?)?[6-9]\d{9}\b')
        }
        self.patterns['phone'] = phone_patterns
        
        # SSN pattern
        self.patterns['ssn'] = re.compile(r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b')
        
        # Credit card patterns
        cc_patterns = {
            'visa': re.compile(r'\b4[0-9]{12}(?:[0-9]{3})?\b'),
            'mastercard': re.compile(r'\b5[1-5][0-9]{14}\b'),
            'amex': re.compile(r'\b3[47][0-9]{13}\b'),
            'discover': re.compile(r'\b6(?:011|5[0-9]{2})[0-9]{12}\b'),
            'generic': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
        }
        self.patterns['credit_card'] = cc_patterns
        
        # Date patterns (for DOB)
        date_patterns = {
            'us_format': re.compile(r'\b(?:0?[1-9]|1[0-2])[/-](?:0?[1-9]|[12]\d|3[01])[/-](?:19|20)\d{2}\b'),
            'iso_format': re.compile(r'\b(?:19|20)\d{2}[-/](?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])\b'),
            'written': re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(?:19|20)\d{2}\b', re.IGNORECASE)
        }
        self.patterns['date'] = date_patterns
        
        # IP address pattern
        self.patterns['ip_address'] = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        )
        
        # Passport number patterns (various countries)
        passport_patterns = {
            'us': re.compile(r'\b[A-Z]{1,2}\d{6,9}\b'),
            'uk': re.compile(r'\b\d{9}\b'),
            'indian': re.compile(r'\b[A-Z]\d{7}\b'),
            'generic': re.compile(r'\b[A-Z0-9]{6,12}\b')
        }
        self.patterns['passport'] = passport_patterns
        
        # Driver license patterns
        dl_patterns = {
            'us_generic': re.compile(r'\b[A-Z]\d{7,8}\b'),
            'numeric': re.compile(r'\b\d{8,12}\b')
        }
        self.patterns['driver_license'] = dl_patterns
        
        # Medical record number patterns
        self.patterns['medical_record'] = re.compile(r'\bMRN:?\s*[A-Z0-9]{6,12}\b', re.IGNORECASE)
        
        # Bank account patterns
        self.patterns['bank_account'] = re.compile(r'\b\d{8,17}\b')
        
        # Insurance ID patterns
        self.patterns['insurance_id'] = re.compile(r'\b[A-Z]{2,3}\d{6,12}\b')
        
        # Name patterns (basic - NER is preferred for names)
        name_patterns = {
            'person': re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'),
            'title_name': re.compile(r'\b(?:Mr|Mrs|Ms|Dr|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b')
        }
        self.patterns['name'] = name_patterns
        
        # Address patterns (basic - NER is preferred for addresses)
        address_patterns = {
            'street': re.compile(r'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Ct|Court)\b', re.IGNORECASE),
            'zip_code': re.compile(r'\b\d{5}(?:-\d{4})?\b'),
            'postal_code': re.compile(r'\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b')  # Canadian postal code
        }
        self.patterns['address'] = address_patterns
        
        logger.info(f"Initialized {len(self.patterns)} pattern categories")
    
    def _initialize_ner_models(self) -> None:
        """Initialize Named Entity Recognition models."""
        try:
            logger.info("Initializing NER models")
            
            # In a real implementation, you would load actual NER models
            # For now, we'll use mock implementations
            self.models['ner_person'] = MockPersonNER()
            self.models['ner_location'] = MockLocationNER()
            self.models['ner_organization'] = MockOrganizationNER()
            
            logger.info("NER models loaded (mock implementations)")
            
        except Exception as e:
            logger.warning(f"Could not load NER models: {e}")
            self.models['ner_person'] = None
            self.models['ner_location'] = None
            self.models['ner_organization'] = None
    
    def _initialize_multilingual_support(self) -> None:
        """Initialize multilingual text processing support."""
        try:
            logger.info("Initializing multilingual support")
            
            # Initialize Indic script patterns if enabled
            if self.config['multilingual']['indic_scripts']:
                self._initialize_indic_patterns()
            
            # In a real implementation, you would load language-specific models
            self.models['multilingual_processor'] = MockMultilingualProcessor()
            
            logger.info("Multilingual support initialized")
            
        except Exception as e:
            logger.warning(f"Could not initialize multilingual support: {e}")
            self.models['multilingual_processor'] = None
    
    def _initialize_indic_patterns(self) -> None:
        """Initialize patterns for Indic scripts."""
        # Devanagari script (Hindi, Marathi, etc.)
        devanagari_name = re.compile(r'[\u0900-\u097F]+(?:\s+[\u0900-\u097F]+)*')
        
        # Bengali script
        bengali_name = re.compile(r'[\u0980-\u09FF]+(?:\s+[\u0980-\u09FF]+)*')
        
        # Tamil script
        tamil_name = re.compile(r'[\u0B80-\u0BFF]+(?:\s+[\u0B80-\u0BFF]+)*')
        
        # Telugu script
        telugu_name = re.compile(r'[\u0C00-\u0C7F]+(?:\s+[\u0C00-\u0C7F]+)*')
        
        # Gujarati script
        gujarati_name = re.compile(r'[\u0A80-\u0AFF]+(?:\s+[\u0A80-\u0AFF]+)*')
        
        # Kannada script
        kannada_name = re.compile(r'[\u0C80-\u0CFF]+(?:\s+[\u0C80-\u0CFF]+)*')
        
        # Malayalam script
        malayalam_name = re.compile(r'[\u0D00-\u0D7F]+(?:\s+[\u0D00-\u0D7F]+)*')
        
        # Oriya script
        oriya_name = re.compile(r'[\u0B00-\u0B7F]+(?:\s+[\u0B00-\u0B7F]+)*')
        
        # Punjabi script (Gurmukhi)
        punjabi_name = re.compile(r'[\u0A00-\u0A7F]+(?:\s+[\u0A00-\u0A7F]+)*')
        
        indic_patterns = {
            'devanagari': devanagari_name,
            'bengali': bengali_name,
            'tamil': tamil_name,
            'telugu': telugu_name,
            'gujarati': gujarati_name,
            'kannada': kannada_name,
            'malayalam': malayalam_name,
            'oriya': oriya_name,
            'punjabi': punjabi_name
        }
        
        self.patterns['indic_names'] = indic_patterns
        
        logger.info(f"Initialized {len(indic_patterns)} Indic script patterns")
    
    def detect_pii(self, document_data: Any) -> List[PIIDetection]:
        """
        Detect text-based PII in document data.
        
        Args:
            document_data: Document data (text string, OCR results, or structured data)
            
        Returns:
            List of PII detections found in the document
        """
        if not self.is_initialized:
            self.initialize()
        
        try:
            # Extract text and coordinate information
            text_data = self._prepare_text_data(document_data)
            if not text_data:
                logger.error("Could not prepare text data for processing")
                return []
            
            detections = []
            
            # Detect emails
            if self.config['email_detection']['enabled']:
                email_detections = self._detect_emails(text_data)
                detections.extend(email_detections)
            
            # Detect phone numbers
            if self.config['phone_detection']['enabled']:
                phone_detections = self._detect_phone_numbers(text_data)
                detections.extend(phone_detections)
            
            # Detect names
            if self.config['name_detection']['enabled']:
                name_detections = self._detect_names(text_data)
                detections.extend(name_detections)
            
            # Detect addresses
            if self.config['address_detection']['enabled']:
                address_detections = self._detect_addresses(text_data)
                detections.extend(address_detections)
            
            # Detect ID numbers
            if self.config['id_detection']['enabled']:
                id_detections = self._detect_id_numbers(text_data)
                detections.extend(id_detections)
            
            # Detect financial information
            if self.config['financial_detection']['enabled']:
                financial_detections = self._detect_financial_info(text_data)
                detections.extend(financial_detections)
            
            # Detect medical information
            if self.config['medical_detection']['enabled']:
                medical_detections = self._detect_medical_info(text_data)
                detections.extend(medical_detections)
            
            # Detect dates of birth
            date_detections = self._detect_dates(text_data)
            detections.extend(date_detections)
            
            # Detect IP addresses
            ip_detections = self._detect_ip_addresses(text_data)
            detections.extend(ip_detections)
            
            # Post-process detections
            detections = self._post_process_detections(detections, text_data)
            
            logger.info(f"NLP engine detected {len(detections)} text PII elements")
            return detections
            
        except Exception as e:
            logger.error(f"Error during NLP PII detection: {e}")
            return []
    
    def _prepare_text_data(self, document_data: Any) -> Optional[Dict[str, Any]]:
        """
        Prepare text data for processing.
        
        Args:
            document_data: Input document data
            
        Returns:
            Dictionary with text and coordinate information, or None if preparation failed
        """
        try:
            if isinstance(document_data, str):
                # Simple text string
                return {
                    'text': document_data,
                    'coordinates': None,
                    'layout_info': None,
                    'pages': [{'text': document_data, 'page_number': 0}]
                }
            
            elif isinstance(document_data, dict):
                # Structured data with text and coordinates
                if 'text' in document_data:
                    return document_data
                elif 'pages' in document_data:
                    # Multi-page document
                    full_text = '\n'.join([page.get('text', '') for page in document_data['pages']])
                    return {
                        'text': full_text,
                        'coordinates': document_data.get('coordinates'),
                        'layout_info': document_data.get('layout_info'),
                        'pages': document_data['pages']
                    }
            
            elif isinstance(document_data, list):
                # List of text segments or OCR results
                if all(isinstance(item, str) for item in document_data):
                    # List of text strings
                    full_text = '\n'.join(document_data)
                    return {
                        'text': full_text,
                        'coordinates': None,
                        'layout_info': None,
                        'pages': [{'text': full_text, 'page_number': 0}]
                    }
                elif all(isinstance(item, dict) for item in document_data):
                    # List of OCR results with coordinates
                    full_text = '\n'.join([item.get('text', '') for item in document_data])
                    return {
                        'text': full_text,
                        'coordinates': document_data,
                        'layout_info': None,
                        'pages': [{'text': full_text, 'page_number': 0, 'segments': document_data}]
                    }
            
            else:
                logger.error(f"Unsupported document data type: {type(document_data)}")
                return None
            
        except Exception as e:
            logger.error(f"Error preparing text data: {e}")
            return None
    
    def _detect_emails(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect email addresses in text."""
        detections = []
        text = text_data['text']
        
        try:
            matches = self.patterns['email'].finditer(text)
            confidence_threshold = self.config['email_detection']['confidence_threshold']
            
            for match in matches:
                email = match.group()
                start, end = match.span()
                
                # Calculate confidence based on email format validity
                confidence = self._calculate_email_confidence(email)
                
                if confidence >= confidence_threshold:
                    # Get coordinates if available
                    bbox = self._get_text_coordinates(start, end, text_data)
                    
                    detection = PIIDetection(
                        type=PIIType.EMAIL,
                        bounding_box=bbox,
                        confidence=confidence,
                        text_content=email,
                        detection_method='nlp',
                        metadata={
                            'pattern_type': 'regex',
                            'text_position': (start, end),
                            'domain': email.split('@')[1] if '@' in email else None
                        }
                    )
                    detections.append(detection)
            
            logger.debug(f"Detected {len(detections)} email addresses")
            
        except Exception as e:
            logger.error(f"Error in email detection: {e}")
        
        return detections
    
    def _detect_phone_numbers(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect phone numbers in text."""
        detections = []
        text = text_data['text']
        
        try:
            confidence_threshold = self.config['phone_detection']['confidence_threshold']
            enabled_formats = self.config['phone_detection']['formats']
            
            for format_name, pattern in self.patterns['phone'].items():
                if format_name not in enabled_formats:
                    continue
                
                matches = pattern.finditer(text)
                
                for match in matches:
                    phone = match.group()
                    start, end = match.span()
                    
                    # Calculate confidence based on format and validation
                    confidence = self._calculate_phone_confidence(phone, format_name)
                    
                    if confidence >= confidence_threshold:
                        bbox = self._get_text_coordinates(start, end, text_data)
                        
                        detection = PIIDetection(
                            type=PIIType.PHONE,
                            bounding_box=bbox,
                            confidence=confidence,
                            text_content=phone,
                            detection_method='nlp',
                            metadata={
                                'pattern_type': 'regex',
                                'format': format_name,
                                'text_position': (start, end),
                                'normalized': self._normalize_phone_number(phone)
                            }
                        )
                        detections.append(detection)
            
            logger.debug(f"Detected {len(detections)} phone numbers")
            
        except Exception as e:
            logger.error(f"Error in phone detection: {e}")
        
        return detections
    
    def _detect_names(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect person and organization names in text."""
        detections = []
        
        try:
            # Use NER if available and enabled
            if (self.config['name_detection'].get('use_ner', False) and 
                self.models.get('ner_person')):
                ner_detections = self._detect_names_ner(text_data)
                detections.extend(ner_detections)
            
            # Use regex patterns as fallback or supplement
            regex_detections = self._detect_names_regex(text_data)
            detections.extend(regex_detections)
            
            # Detect Indic script names if enabled
            if self.config['multilingual']['indic_scripts']:
                indic_detections = self._detect_indic_names(text_data)
                detections.extend(indic_detections)
            
            logger.debug(f"Detected {len(detections)} names")
            
        except Exception as e:
            logger.error(f"Error in name detection: {e}")
        
        return detections
    
    def _detect_names_ner(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect names using NER models."""
        detections = []
        text = text_data['text']
        
        try:
            ner_person = self.models.get('ner_person')
            if not ner_person:
                return detections
            
            # Get person entities from NER
            entities = ner_person.extract_entities(text)
            confidence_threshold = self.config['name_detection']['confidence_threshold']
            
            for entity in entities:
                if entity['confidence'] >= confidence_threshold:
                    bbox = self._get_text_coordinates(
                        entity['start'], entity['end'], text_data
                    )
                    
                    detection = PIIDetection(
                        type=PIIType.NAME,
                        bounding_box=bbox,
                        confidence=entity['confidence'],
                        text_content=entity['text'],
                        detection_method='nlp',
                        metadata={
                            'pattern_type': 'ner',
                            'entity_type': entity['type'],
                            'text_position': (entity['start'], entity['end'])
                        }
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"Error in NER name detection: {e}")
        
        return detections
    
    def _detect_names_regex(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect names using regex patterns."""
        detections = []
        text = text_data['text']
        
        try:
            confidence_threshold = self.config['name_detection']['confidence_threshold']
            min_length = self.config['name_detection']['min_length']
            max_length = self.config['name_detection']['max_length']
            
            for pattern_name, pattern in self.patterns['name'].items():
                matches = pattern.finditer(text)
                
                for match in matches:
                    name = match.group().strip()
                    start, end = match.span()
                    
                    # Filter by length
                    if not (min_length <= len(name) <= max_length):
                        continue
                    
                    # Calculate confidence
                    confidence = self._calculate_name_confidence(name, pattern_name)
                    
                    if confidence >= confidence_threshold:
                        bbox = self._get_text_coordinates(start, end, text_data)
                        
                        detection = PIIDetection(
                            type=PIIType.NAME,
                            bounding_box=bbox,
                            confidence=confidence,
                            text_content=name,
                            detection_method='nlp',
                            metadata={
                                'pattern_type': 'regex',
                                'pattern_name': pattern_name,
                                'text_position': (start, end)
                            }
                        )
                        detections.append(detection)
            
        except Exception as e:
            logger.error(f"Error in regex name detection: {e}")
        
        return detections
    
    def _detect_indic_names(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect names in Indic scripts."""
        detections = []
        text = text_data['text']
        
        try:
            if 'indic_names' not in self.patterns:
                return detections
            
            confidence_threshold = self.config['name_detection']['confidence_threshold']
            
            for script_name, pattern in self.patterns['indic_names'].items():
                matches = pattern.finditer(text)
                
                for match in matches:
                    name = match.group().strip()
                    start, end = match.span()
                    
                    # Basic validation for Indic names
                    if len(name) < 2:
                        continue
                    
                    confidence = 0.8  # High confidence for Indic script matches
                    
                    if confidence >= confidence_threshold:
                        bbox = self._get_text_coordinates(start, end, text_data)
                        
                        detection = PIIDetection(
                            type=PIIType.NAME,
                            bounding_box=bbox,
                            confidence=confidence,
                            text_content=name,
                            detection_method='nlp',
                            metadata={
                                'pattern_type': 'indic_regex',
                                'script': script_name,
                                'text_position': (start, end)
                            }
                        )
                        detections.append(detection)
            
        except Exception as e:
            logger.error(f"Error in Indic name detection: {e}")
        
        return detections
    
    def _detect_addresses(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect addresses in text."""
        detections = []
        
        try:
            # Use NER if available
            if (self.config['address_detection'].get('use_ner', False) and 
                self.models.get('ner_location')):
                ner_detections = self._detect_addresses_ner(text_data)
                detections.extend(ner_detections)
            
            # Use regex patterns
            regex_detections = self._detect_addresses_regex(text_data)
            detections.extend(regex_detections)
            
            logger.debug(f"Detected {len(detections)} addresses")
            
        except Exception as e:
            logger.error(f"Error in address detection: {e}")
        
        return detections
    
    def _detect_addresses_ner(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect addresses using NER models."""
        detections = []
        text = text_data['text']
        
        try:
            ner_location = self.models.get('ner_location')
            if not ner_location:
                return detections
            
            entities = ner_location.extract_entities(text)
            confidence_threshold = self.config['address_detection']['confidence_threshold']
            
            for entity in entities:
                if entity['confidence'] >= confidence_threshold:
                    bbox = self._get_text_coordinates(
                        entity['start'], entity['end'], text_data
                    )
                    
                    detection = PIIDetection(
                        type=PIIType.ADDRESS,
                        bounding_box=bbox,
                        confidence=entity['confidence'],
                        text_content=entity['text'],
                        detection_method='nlp',
                        metadata={
                            'pattern_type': 'ner',
                            'entity_type': entity['type'],
                            'text_position': (entity['start'], entity['end'])
                        }
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"Error in NER address detection: {e}")
        
        return detections
    
    def _detect_addresses_regex(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect addresses using regex patterns."""
        detections = []
        text = text_data['text']
        
        try:
            confidence_threshold = self.config['address_detection']['confidence_threshold']
            
            for pattern_name, pattern in self.patterns['address'].items():
                matches = pattern.finditer(text)
                
                for match in matches:
                    address = match.group().strip()
                    start, end = match.span()
                    
                    confidence = self._calculate_address_confidence(address, pattern_name)
                    
                    if confidence >= confidence_threshold:
                        bbox = self._get_text_coordinates(start, end, text_data)
                        
                        detection = PIIDetection(
                            type=PIIType.ADDRESS,
                            bounding_box=bbox,
                            confidence=confidence,
                            text_content=address,
                            detection_method='nlp',
                            metadata={
                                'pattern_type': 'regex',
                                'pattern_name': pattern_name,
                                'text_position': (start, end)
                            }
                        )
                        detections.append(detection)
            
        except Exception as e:
            logger.error(f"Error in regex address detection: {e}")
        
        return detections
    
    def _detect_id_numbers(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect various ID numbers (SSN, passport, driver license, etc.)."""
        detections = []
        text = text_data['text']
        
        try:
            confidence_threshold = self.config['id_detection']['confidence_threshold']
            enabled_types = self.config['id_detection']['types']
            
            # Detect SSN
            if 'ssn' in enabled_types:
                ssn_detections = self._detect_pattern_matches(
                    text, text_data, self.patterns['ssn'], PIIType.SSN, 
                    confidence_threshold, 'ssn'
                )
                detections.extend(ssn_detections)
            
            # Detect passport numbers
            if 'passport' in enabled_types:
                for pattern_name, pattern in self.patterns['passport'].items():
                    passport_detections = self._detect_pattern_matches(
                        text, text_data, pattern, PIIType.PASSPORT_NUMBER,
                        confidence_threshold, f'passport_{pattern_name}'
                    )
                    detections.extend(passport_detections)
            
            # Detect driver license numbers
            if 'driver_license' in enabled_types:
                for pattern_name, pattern in self.patterns['driver_license'].items():
                    dl_detections = self._detect_pattern_matches(
                        text, text_data, pattern, PIIType.DRIVER_LICENSE,
                        confidence_threshold, f'driver_license_{pattern_name}'
                    )
                    detections.extend(dl_detections)
            
            logger.debug(f"Detected {len(detections)} ID numbers")
            
        except Exception as e:
            logger.error(f"Error in ID number detection: {e}")
        
        return detections
    
    def _detect_financial_info(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect financial information (credit cards, bank accounts, etc.)."""
        detections = []
        text = text_data['text']
        
        try:
            confidence_threshold = self.config['financial_detection']['confidence_threshold']
            enabled_types = self.config['financial_detection']['types']
            
            # Detect credit card numbers
            if 'credit_card' in enabled_types:
                for cc_type, pattern in self.patterns['credit_card'].items():
                    matches = pattern.finditer(text)
                    
                    for match in matches:
                        cc_number = match.group().strip()
                        start, end = match.span()
                        
                        # Validate using Luhn algorithm
                        if self._validate_credit_card(cc_number):
                            confidence = 0.95  # High confidence for validated CC
                            
                            if confidence >= confidence_threshold:
                                bbox = self._get_text_coordinates(start, end, text_data)
                                
                                detection = PIIDetection(
                                    type=PIIType.CREDIT_CARD,
                                    bounding_box=bbox,
                                    confidence=confidence,
                                    text_content=cc_number,
                                    detection_method='nlp',
                                    metadata={
                                        'pattern_type': 'regex',
                                        'cc_type': cc_type,
                                        'text_position': (start, end),
                                        'luhn_valid': True
                                    }
                                )
                                detections.append(detection)
            
            # Detect bank account numbers
            if 'bank_account' in enabled_types:
                bank_detections = self._detect_pattern_matches(
                    text, text_data, self.patterns['bank_account'], PIIType.BANK_ACCOUNT,
                    confidence_threshold, 'bank_account'
                )
                detections.extend(bank_detections)
            
            logger.debug(f"Detected {len(detections)} financial information items")
            
        except Exception as e:
            logger.error(f"Error in financial info detection: {e}")
        
        return detections
    
    def _detect_medical_info(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect medical information (MRN, insurance IDs, etc.)."""
        detections = []
        text = text_data['text']
        
        try:
            confidence_threshold = self.config['medical_detection']['confidence_threshold']
            
            # Detect medical record numbers
            mrn_detections = self._detect_pattern_matches(
                text, text_data, self.patterns['medical_record'], 
                PIIType.MEDICAL_RECORD_NUMBER, confidence_threshold, 'medical_record'
            )
            detections.extend(mrn_detections)
            
            # Detect insurance IDs
            insurance_detections = self._detect_pattern_matches(
                text, text_data, self.patterns['insurance_id'], 
                PIIType.INSURANCE_ID, confidence_threshold, 'insurance_id'
            )
            detections.extend(insurance_detections)
            
            logger.debug(f"Detected {len(detections)} medical information items")
            
        except Exception as e:
            logger.error(f"Error in medical info detection: {e}")
        
        return detections
    
    def _detect_dates(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect dates (potential dates of birth)."""
        detections = []
        text = text_data['text']
        
        try:
            confidence_threshold = 0.7  # Lower threshold for dates
            
            for pattern_name, pattern in self.patterns['date'].items():
                matches = pattern.finditer(text)
                
                for match in matches:
                    date_str = match.group().strip()
                    start, end = match.span()
                    
                    # Check if this could be a date of birth (reasonable year range)
                    if self._is_potential_dob(date_str):
                        confidence = 0.8
                        
                        if confidence >= confidence_threshold:
                            bbox = self._get_text_coordinates(start, end, text_data)
                            
                            detection = PIIDetection(
                                type=PIIType.DATE_OF_BIRTH,
                                bounding_box=bbox,
                                confidence=confidence,
                                text_content=date_str,
                                detection_method='nlp',
                                metadata={
                                    'pattern_type': 'regex',
                                    'date_format': pattern_name,
                                    'text_position': (start, end)
                                }
                            )
                            detections.append(detection)
            
            logger.debug(f"Detected {len(detections)} potential dates of birth")
            
        except Exception as e:
            logger.error(f"Error in date detection: {e}")
        
        return detections
    
    def _detect_ip_addresses(self, text_data: Dict[str, Any]) -> List[PIIDetection]:
        """Detect IP addresses."""
        detections = []
        text = text_data['text']
        
        try:
            confidence_threshold = 0.9  # High confidence for IP addresses
            
            ip_detections = self._detect_pattern_matches(
                text, text_data, self.patterns['ip_address'], PIIType.IP_ADDRESS,
                confidence_threshold, 'ip_address'
            )
            detections.extend(ip_detections)
            
            logger.debug(f"Detected {len(detections)} IP addresses")
            
        except Exception as e:
            logger.error(f"Error in IP address detection: {e}")
        
        return detections
    
    def _detect_pattern_matches(
        self, text: str, text_data: Dict[str, Any], pattern: Pattern,
        pii_type: PIIType, confidence_threshold: float, pattern_name: str
    ) -> List[PIIDetection]:
        """Generic method to detect pattern matches."""
        detections = []
        
        try:
            matches = pattern.finditer(text)
            
            for match in matches:
                matched_text = match.group().strip()
                start, end = match.span()
                
                confidence = self._calculate_pattern_confidence(matched_text, pattern_name)
                
                if confidence >= confidence_threshold:
                    bbox = self._get_text_coordinates(start, end, text_data)
                    
                    detection = PIIDetection(
                        type=pii_type,
                        bounding_box=bbox,
                        confidence=confidence,
                        text_content=matched_text,
                        detection_method='nlp',
                        metadata={
                            'pattern_type': 'regex',
                            'pattern_name': pattern_name,
                            'text_position': (start, end)
                        }
                    )
                    detections.append(detection)
            
        except Exception as e:
            logger.error(f"Error in pattern matching for {pattern_name}: {e}")
        
        return detections
    
    def _get_text_coordinates(
        self, start: int, end: int, text_data: Dict[str, Any]
    ) -> BoundingBox:
        """
        Get bounding box coordinates for text position.
        
        Args:
            start: Start position in text
            end: End position in text
            text_data: Text data with coordinate information
            
        Returns:
            BoundingBox for the text region
        """
        # If no coordinate information available, create a default bounding box
        if not text_data.get('coordinates') or not self.config['layout_awareness']['use_coordinates']:
            # Create a synthetic bounding box based on text position
            line_height = 20
            char_width = 8
            
            # Estimate line and column from character position
            text_before = text_data['text'][:start]
            line_number = text_before.count('\n')
            line_start = text_before.rfind('\n') + 1
            column_start = start - line_start
            column_end = column_start + (end - start)
            
            x1 = column_start * char_width
            y1 = line_number * line_height
            x2 = column_end * char_width
            y2 = y1 + line_height
            
            return BoundingBox(x1, y1, x2, y2)
        
        # Use actual coordinate information if available
        coordinates = text_data['coordinates']
        
        # This is a simplified implementation
        # In a real system, you would map text positions to actual coordinates
        # from OCR or layout analysis results
        
        # For now, return a default bounding box
        return BoundingBox(0, 0, 100, 20)
    
    def _post_process_detections(
        self, detections: List[PIIDetection], text_data: Dict[str, Any]
    ) -> List[PIIDetection]:
        """Post-process detections to remove duplicates and merge nearby detections."""
        if not detections:
            return detections
        
        try:
            # Remove duplicates based on text content and position
            unique_detections = self._remove_duplicate_detections(detections)
            
            # Merge nearby detections if enabled
            if self.config['layout_awareness']['merge_nearby_detections']:
                merged_detections = self._merge_nearby_detections(unique_detections)
                return merged_detections
            
            return unique_detections
            
        except Exception as e:
            logger.error(f"Error in post-processing detections: {e}")
            return detections
    
    def _remove_duplicate_detections(self, detections: List[PIIDetection]) -> List[PIIDetection]:
        """Remove duplicate detections based on text content and overlap."""
        if len(detections) <= 1:
            return detections
        
        unique_detections = []
        
        for detection in detections:
            is_duplicate = False
            
            for existing in unique_detections:
                # Check if same type and overlapping text
                if (detection.type == existing.type and
                    detection.text_content == existing.text_content and
                    detection.overlaps_with(existing, threshold=0.5)):
                    
                    # Keep the one with higher confidence
                    if detection.confidence > existing.confidence:
                        unique_detections.remove(existing)
                        unique_detections.append(detection)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_detections.append(detection)
        
        return unique_detections
    
    def _merge_nearby_detections(self, detections: List[PIIDetection]) -> List[PIIDetection]:
        """Merge nearby detections of the same type."""
        if len(detections) <= 1:
            return detections
        
        merged_detections = []
        proximity_threshold = self.config['layout_awareness']['proximity_threshold']
        
        # Group detections by type
        type_groups = {}
        for detection in detections:
            if detection.type not in type_groups:
                type_groups[detection.type] = []
            type_groups[detection.type].append(detection)
        
        # Process each type group
        for pii_type, group_detections in type_groups.items():
            if len(group_detections) == 1:
                merged_detections.extend(group_detections)
                continue
            
            # Find nearby detections to merge
            processed = set()
            
            for i, detection in enumerate(group_detections):
                if i in processed:
                    continue
                
                merge_candidates = [detection]
                
                for j, other_detection in enumerate(group_detections[i+1:], i+1):
                    if j in processed:
                        continue
                    
                    # Check if detections are nearby
                    if self._are_detections_nearby(detection, other_detection, proximity_threshold):
                        merge_candidates.append(other_detection)
                        processed.add(j)
                
                # Merge candidates if more than one
                if len(merge_candidates) > 1:
                    merged_detection = self._merge_detection_group(merge_candidates)
                    merged_detections.append(merged_detection)
                else:
                    merged_detections.append(detection)
                
                processed.add(i)
        
        return merged_detections
    
    def _are_detections_nearby(
        self, det1: PIIDetection, det2: PIIDetection, threshold: int
    ) -> bool:
        """Check if two detections are nearby based on their bounding boxes."""
        center1 = det1.center
        center2 = det2.center
        
        distance = ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5
        return distance <= threshold
    
    def _merge_detection_group(self, detections: List[PIIDetection]) -> PIIDetection:
        """Merge a group of detections into a single detection."""
        if len(detections) == 1:
            return detections[0]
        
        # Use the detection with highest confidence as base
        base_detection = max(detections, key=lambda d: d.confidence)
        
        # Merge bounding boxes
        x1_min = min(d.bounding_box.x1 for d in detections)
        y1_min = min(d.bounding_box.y1 for d in detections)
        x2_max = max(d.bounding_box.x2 for d in detections)
        y2_max = max(d.bounding_box.y2 for d in detections)
        
        merged_bbox = BoundingBox(x1_min, y1_min, x2_max, y2_max)
        
        # Merge text content
        merged_text = ' '.join([d.text_content for d in detections if d.text_content])
        
        # Calculate average confidence
        avg_confidence = sum(d.confidence for d in detections) / len(detections)
        
        # Merge metadata
        merged_metadata = base_detection.metadata.copy()
        merged_metadata['merged_from'] = [d.id for d in detections]
        merged_metadata['merged_count'] = len(detections)
        
        return PIIDetection(
            type=base_detection.type,
            bounding_box=merged_bbox,
            confidence=avg_confidence,
            text_content=merged_text,
            detection_method='nlp',
            metadata=merged_metadata
        )
    
    # Confidence calculation methods
    
    def _calculate_email_confidence(self, email: str) -> float:
        """Calculate confidence score for email detection."""
        confidence = 0.9  # Base confidence for regex match
        
        # Boost confidence for common domains
        domain = email.split('@')[1].lower() if '@' in email else ''
        common_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'company.com']
        
        if any(domain.endswith(cd) for cd in common_domains):
            confidence = min(1.0, confidence + 0.05)
        
        # Reduce confidence for suspicious patterns
        if '..' in email or email.startswith('.') or email.endswith('.'):
            confidence -= 0.2
        
        return max(0.0, confidence)
    
    def _calculate_phone_confidence(self, phone: str, format_name: str) -> float:
        """Calculate confidence score for phone number detection."""
        base_confidence = {
            'us': 0.85,
            'international': 0.8,
            'indian': 0.9
        }.get(format_name, 0.7)
        
        # Boost confidence for well-formatted numbers
        if '-' in phone or '(' in phone or '+' in phone:
            base_confidence = min(1.0, base_confidence + 0.05)
        
        return base_confidence
    
    def _calculate_name_confidence(self, name: str, pattern_name: str) -> float:
        """Calculate confidence score for name detection."""
        base_confidence = {
            'person': 0.6,
            'title_name': 0.8
        }.get(pattern_name, 0.5)
        
        # Boost confidence for proper capitalization
        if name.istitle():
            base_confidence = min(1.0, base_confidence + 0.1)
        
        # Reduce confidence for all caps or all lowercase
        if name.isupper() or name.islower():
            base_confidence -= 0.2
        
        return max(0.0, base_confidence)
    
    def _calculate_address_confidence(self, address: str, pattern_name: str) -> float:
        """Calculate confidence score for address detection."""
        base_confidence = {
            'street': 0.8,
            'zip_code': 0.9,
            'postal_code': 0.9
        }.get(pattern_name, 0.7)
        
        return base_confidence
    
    def _calculate_pattern_confidence(self, text: str, pattern_name: str) -> float:
        """Calculate confidence score for generic pattern matches."""
        # Default confidence based on pattern type
        confidence_map = {
            'ssn': 0.9,
            'ip_address': 0.95,
            'medical_record': 0.8,
            'insurance_id': 0.8,
            'bank_account': 0.7
        }
        
        return confidence_map.get(pattern_name, 0.8)
    
    def _validate_credit_card(self, cc_number: str) -> bool:
        """Validate credit card number using Luhn algorithm."""
        # Remove spaces and dashes
        cc_number = re.sub(r'[-\s]', '', cc_number)
        
        if not cc_number.isdigit():
            return False
        
        # Luhn algorithm
        def luhn_checksum(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        return luhn_checksum(cc_number) == 0
    
    def _is_potential_dob(self, date_str: str) -> bool:
        """Check if a date could be a date of birth (reasonable year range)."""
        # Extract year from date string
        year_match = re.search(r'(19|20)\d{2}', date_str)
        if not year_match:
            return False
        
        year = int(year_match.group())
        current_year = 2024  # Could be made dynamic
        
        # Reasonable DOB range: 1900 to current year - 5
        return 1900 <= year <= (current_year - 5)
    
    def _normalize_phone_number(self, phone: str) -> str:
        """Normalize phone number to standard format."""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Format based on length
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone  # Return original if can't normalize
    
    def get_supported_types(self) -> List[str]:
        """
        Get list of PII types this engine can detect.
        
        Returns:
            List of supported PII type names
        """
        supported_types = []
        
        if self.config['email_detection']['enabled']:
            supported_types.append(PIIType.EMAIL.value)
        
        if self.config['phone_detection']['enabled']:
            supported_types.append(PIIType.PHONE.value)
        
        if self.config['name_detection']['enabled']:
            supported_types.append(PIIType.NAME.value)
        
        if self.config['address_detection']['enabled']:
            supported_types.append(PIIType.ADDRESS.value)
        
        if self.config['id_detection']['enabled']:
            id_types = self.config['id_detection']['types']
            if 'ssn' in id_types:
                supported_types.append(PIIType.SSN.value)
            if 'passport' in id_types:
                supported_types.append(PIIType.PASSPORT_NUMBER.value)
            if 'driver_license' in id_types:
                supported_types.append(PIIType.DRIVER_LICENSE.value)
        
        if self.config['financial_detection']['enabled']:
            financial_types = self.config['financial_detection']['types']
            if 'credit_card' in financial_types:
                supported_types.append(PIIType.CREDIT_CARD.value)
            if 'bank_account' in financial_types:
                supported_types.append(PIIType.BANK_ACCOUNT.value)
        
        if self.config['medical_detection']['enabled']:
            supported_types.extend([
                PIIType.MEDICAL_RECORD_NUMBER.value,
                PIIType.INSURANCE_ID.value
            ])
        
        # Always supported
        supported_types.extend([
            PIIType.DATE_OF_BIRTH.value,
            PIIType.IP_ADDRESS.value
        ])
        
        return supported_types
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the AI engine with given parameters.
        
        Args:
            config: Configuration dictionary
        """
        self.config.update(config)
        self._merge_config()
        
        # Reinitialize if already initialized
        if self.is_initialized:
            self.is_initialized = False
            self.initialize()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about loaded models and patterns.
        
        Returns:
            Dictionary with model and pattern information
        """
        return {
            'patterns': {
                'loaded_patterns': list(self.patterns.keys()),
                'pattern_count': len(self.patterns)
            },
            'ner_models': {
                'person_ner': 'ner_person' in self.models and self.models['ner_person'] is not None,
                'location_ner': 'ner_location' in self.models and self.models['ner_location'] is not None,
                'organization_ner': 'ner_organization' in self.models and self.models['ner_organization'] is not None
            },
            'multilingual': {
                'enabled': self.config['multilingual']['enabled'],
                'languages': self.config['multilingual']['languages'],
                'indic_scripts': self.config['multilingual']['indic_scripts'],
                'processor_loaded': 'multilingual_processor' in self.models and self.models['multilingual_processor'] is not None
            },
            'detection_capabilities': {
                'email': self.config['email_detection']['enabled'],
                'phone': self.config['phone_detection']['enabled'],
                'names': self.config['name_detection']['enabled'],
                'addresses': self.config['address_detection']['enabled'],
                'id_numbers': self.config['id_detection']['enabled'],
                'financial': self.config['financial_detection']['enabled'],
                'medical': self.config['medical_detection']['enabled']
            }
        }


# Mock implementations for testing and development

class MockPersonNER:
    """Mock person NER model for testing purposes."""
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Mock person entity extraction."""
        entities = []
        
        # Simple mock: find capitalized words that could be names
        import re
        name_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b')
        
        for match in name_pattern.finditer(text):
            name = match.group()
            start, end = match.span()
            
            # Skip common non-name phrases
            skip_phrases = ['New York', 'United States', 'San Francisco', 'Los Angeles']
            if name in skip_phrases:
                continue
            
            entities.append({
                'text': name,
                'start': start,
                'end': end,
                'type': 'PERSON',
                'confidence': 0.8
            })
        
        return entities


class MockLocationNER:
    """Mock location NER model for testing purposes."""
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Mock location entity extraction."""
        entities = []
        
        # Simple mock: find common location patterns
        location_keywords = ['Street', 'Avenue', 'Road', 'Boulevard', 'Drive', 'Lane', 'Court']
        
        import re
        for keyword in location_keywords:
            pattern = re.compile(rf'\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+{keyword}\b', re.IGNORECASE)
            
            for match in pattern.finditer(text):
                location = match.group()
                start, end = match.span()
                
                entities.append({
                    'text': location,
                    'start': start,
                    'end': end,
                    'type': 'LOCATION',
                    'confidence': 0.75
                })
        
        return entities


class MockOrganizationNER:
    """Mock organization NER model for testing purposes."""
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Mock organization entity extraction."""
        entities = []
        
        # Simple mock: find organization patterns
        org_suffixes = ['Inc', 'Corp', 'LLC', 'Ltd', 'Company', 'Corporation']
        
        import re
        for suffix in org_suffixes:
            pattern = re.compile(rf'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+{suffix}\.?\b')
            
            for match in pattern.finditer(text):
                org = match.group()
                start, end = match.span()
                
                entities.append({
                    'text': org,
                    'start': start,
                    'end': end,
                    'type': 'ORGANIZATION',
                    'confidence': 0.7
                })
        
        return entities


class MockMultilingualProcessor:
    """Mock multilingual processor for testing purposes."""
    
    def __init__(self):
        """Initialize mock multilingual processor."""
        self.supported_languages = ['en', 'hi', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml', 'or', 'pa']
    
    def detect_language(self, text: str) -> str:
        """Mock language detection."""
        # Simple heuristic: check for Indic script characters
        if any('\u0900' <= char <= '\u097F' for char in text):  # Devanagari
            return 'hi'
        elif any('\u0980' <= char <= '\u09FF' for char in text):  # Bengali
            return 'bn'
        elif any('\u0B80' <= char <= '\u0BFF' for char in text):  # Tamil
            return 'ta'
        else:
            return 'en'
    
    def process_multilingual_text(self, text: str) -> Dict[str, Any]:
        """Mock multilingual text processing."""
        language = self.detect_language(text)
        
        return {
            'detected_language': language,
            'confidence': 0.9,
            'script_type': 'indic' if language != 'en' else 'latin',
            'processed_text': text  # In real implementation, this might be normalized
        }