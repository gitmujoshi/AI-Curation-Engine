"""
PII Detection & Sanitization

Uses Microsoft Presidio for ML-based Named Entity Recognition
to detect and anonymize sensitive information with high accuracy.
"""

import logging
import re
from typing import Dict, List, Tuple, Set, Optional
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)


class PIIDetector:
    """
    ML-powered PII detection and sanitization using Microsoft Presidio.
    
    Detects:
    - Social Security Numbers (US)
    - Credit Card Numbers (all major issuers)
    - Email Addresses
    - Phone Numbers (US/International)
    - Physical Addresses
    - Personal Names (via NER)
    - Medical License Numbers
    - API Keys and Secrets
    - IP Addresses
    - IBAN, Crypto Wallets
    
    Uses:
    - spaCy NER models for context-aware detection
    - Pattern matching for structured identifiers
    - ML-based scoring to reduce false positives
    """
    
    # Additional regex patterns for tech-specific PII
    TECH_PATTERNS = {
        "aws_key": re.compile(r'AKIA[0-9A-Z]{16}'),
        "github_token": re.compile(r'ghp_[A-Za-z0-9]{36}'),
        "slack_token": re.compile(r'xox[baprs]-[0-9a-zA-Z]{10,48}'),
        "jwt": re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'),
        "private_key": re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    }
    
    TECH_REPLACEMENTS = {
        "aws_key": "[AWS_ACCESS_KEY_REDACTED]",
        "github_token": "[GITHUB_TOKEN_REDACTED]",
        "slack_token": "[SLACK_TOKEN_REDACTED]",
        "jwt": "[JWT_TOKEN_REDACTED]",
        "private_key": "[PRIVATE_KEY_REDACTED]",
    }
    
    def __init__(self, languages: List[str] = ["en"], score_threshold: float = 0.5):
        """
        Initialize Presidio-based PII detector.
        
        Args:
            languages: List of language codes (e.g., ["en", "es"])
            score_threshold: Minimum confidence score (0.0-1.0)
        """
        try:
            # Initialize NLP engine with spaCy
            nlp_configuration = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": lang, "model_name": f"{lang}_core_web_sm"} for lang in languages]
            }
            
            provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
            nlp_engine = provider.create_engine()
            
            # Initialize analyzer with all recognizers
            self.analyzer = AnalyzerEngine(
                nlp_engine=nlp_engine,
                supported_languages=languages
            )
            
            # Initialize anonymizer
            self.anonymizer = AnonymizerEngine()
            
            self.score_threshold = score_threshold
            self.languages = languages
            
            logger.info(
                f"Initialized Presidio PII detector with languages: {languages}, "
                f"threshold: {score_threshold}"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize Presidio: {e}")
            logger.warning("Falling back to regex-only PII detection")
            self.analyzer = None
            self.anonymizer = None
    
    async def detect(self, text: str, language: str = "en") -> List[Tuple[str, str, float]]:
        """
        Detect PII in text using ML-powered analysis.
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            List of (pii_type, matched_text, confidence_score) tuples
        """
        detected = []
        
        # Presidio-based detection
        if self.analyzer:
            try:
                results = self.analyzer.analyze(
                    text=text,
                    language=language,
                    score_threshold=self.score_threshold
                )
                
                for result in results:
                    entity_text = text[result.start:result.end]
                    detected.append((
                        result.entity_type,
                        entity_text,
                        result.score
                    ))
                    
            except Exception as e:
                logger.error(f"Presidio analysis failed: {e}")
        
        # Additional tech-specific pattern matching
        for pii_type, pattern in self.TECH_PATTERNS.items():
            matches = pattern.finditer(text)
            for match in matches:
                detected.append((
                    pii_type,
                    match.group(),
                    1.0  # High confidence for pattern matches
                ))
        
        if detected:
            logger.debug(f"Detected {len(detected)} PII entities")
        
        return detected
    async def sanitize(self, text: str, language: str = "en") -> str:
        """
        Sanitize text by replacing PII with redaction markers.
        
        Uses Presidio's anonymizer for ML-powered redaction with
        context-aware replacement.
        
        Args:
            text: Text to sanitize
            language: Language code
            
        Returns:
            Sanitized text with PII replaced by type-specific markers
        """
        if not text:
            return text
        
        sanitized = text
        
        # Presidio-based anonymization
        if self.analyzer and self.anonymizer:
            try:
                # Analyze text
                analyzer_results = self.analyzer.analyze(
                    text=text,
                    language=language,
                    score_threshold=self.score_threshold
                )
                
                if analyzer_results:
                    # Create anonymization operators (custom replacements by type)
                    operators = {}
                    for result in analyzer_results:
                        entity_type = result.entity_type
                        operators[entity_type] = OperatorConfig(
                            "replace",
                            {
                                "new_value": f"[{entity_type}_REDACTED]"
                            }
                        )
                    
                    # Anonymize
                    anonymized_result = self.anonymizer.anonymize(
                        text=text,
                        analyzer_results=analyzer_results,
                        operators=operators
                    )
                    
                    sanitized = anonymized_result.text
                    
                    # Log what was sanitized
                    entity_types = [r.entity_type for r in analyzer_results]
                    logger.warning(
                        f"Presidio detected and sanitized {len(analyzer_results)} PII instances: "
                        f"{entity_types}"
                    )
                    
            except Exception as e:
                logger.error(f"Presidio anonymization failed: {e}")
                # Fall through to regex-based sanitization
        
        # Additional tech-specific sanitization
        for pii_type, pattern in self.TECH_PATTERNS.items():
            replacement = self.TECH_REPLACEMENTS[pii_type]
            new_text = pattern.sub(replacement, sanitized)
            if new_text != sanitized:
                logger.warning(f"Detected and sanitized {pii_type}")
                sanitized = new_text
        
        return sanitized
    
    async def analyze(self, text: str, language: str = "en") -> Dict[str, int]:
        """
        Analyze text for PII without sanitizing.
        
        Returns detailed statistics about PII types found.
        
        Args:
            text: Text to analyze
            language: Language code
            
        Returns:
            Dictionary of pii_type -> count, plus metadata
        """
        counts = {}
        total_entities = 0
        high_confidence = 0
        
        # Presidio analysis
        if self.analyzer:
            try:
                results = self.analyzer.analyze(
                    text=text,
                    language=language,
                    score_threshold=self.score_threshold
                )
                
                for result in results:
                    entity_type = result.entity_type
                    counts[entity_type] = counts.get(entity_type, 0) + 1
                    total_entities += 1
                    
                    if result.score >= 0.85:
                        high_confidence += 1
                        
            except Exception as e:
                logger.error(f"Presidio analysis failed: {e}")
        
        # Tech-specific patterns
        for pii_type, pattern in self.TECH_PATTERNS.items():
            matches = list(pattern.finditer(text))
            if matches:
                counts[pii_type] = len(matches)
                total_entities += len(matches)
                high_confidence += len(matches)  # Patterns are high confidence
        
        # Add metadata
        if total_entities > 0:
            counts["_metadata"] = {
                "total_entities": total_entities,
                "high_confidence_entities": high_confidence,
                "confidence_rate": high_confidence / total_entities if total_entities > 0 else 0,
                "unique_types": len([k for k in counts.keys() if k != "_metadata"])
            }
        
        return counts
    
    def get_supported_entities(self) -> List[str]:
        """
        Get list of all PII entity types this detector supports.
        
        Returns:
            List of entity type names
        """
        if self.analyzer:
            return self.analyzer.get_supported_entities()
        else:
            return list(self.TECH_PATTERNS.keys())
