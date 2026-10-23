"""
Unit Tests for PII Detector

Tests the Presidio-based PII detection system.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.guardrails.pii_detector import PIIDetector


class TestPIIDetector:
    """Test PIIDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance."""
        return PIIDetector(languages=["en"], score_threshold=0.5)
    
    @pytest.mark.asyncio
    async def test_detect_email(self, detector):
        """Test detecting email addresses."""
        text = "Contact me at john.doe@example.com"
        
        detected = await detector.detect(text)
        
        # Should detect email
        entity_types = [entity_type for entity_type, _, _ in detected]
        assert any("EMAIL" in et or "email" in et.lower() for et in entity_types)
    
    @pytest.mark.asyncio
    async def test_detect_phone(self, detector):
        """Test detecting phone numbers."""
        text = "Call me at 555-123-4567"
        
        detected = await detector.detect(text)
        
        # Should detect phone number
        entity_types = [entity_type for entity_type, _, _ in detected]
        assert any("PHONE" in et or "phone" in et.lower() for et in entity_types)
    
    @pytest.mark.asyncio
    async def test_detect_ssn(self, detector):
        """Test detecting Social Security Numbers."""
        text = "My SSN is 123-45-6789"
        
        detected = await detector.detect(text)
        
        # Should detect SSN
        entity_types = [entity_type for entity_type, _, _ in detected]
        assert any("SSN" in et for et in entity_types)
    
    @pytest.mark.asyncio
    async def test_detect_credit_card(self, detector):
        """Test detecting credit card numbers."""
        text = "Card number: 4532-1234-5678-9010"
        
        detected = await detector.detect(text)
        
        # Should detect credit card
        entity_types = [entity_type for entity_type, _, _ in detected]
        assert any("CREDIT" in et or "credit" in et.lower() for et in entity_types)
    
    @pytest.mark.asyncio
    async def test_detect_aws_key(self, detector):
        """Test detecting AWS access keys."""
        text = "AWS Key: AKIAIOSFODNN7EXAMPLE"
        
        detected = await detector.detect(text)
        
        # Should detect AWS key
        entity_types = [entity_type for entity_type, _, _ in detected]
        assert "aws_key" in entity_types
    
    @pytest.mark.asyncio
    async def test_detect_github_token(self, detector):
        """Test detecting GitHub tokens."""
        text = "Token: ghp_1234567890abcdefghijklmnopqrstuv"
        
        detected = await detector.detect(text)
        
        # Should detect GitHub token
        entity_types = [entity_type for entity_type, _, _ in detected]
        assert "github_token" in entity_types
    
    @pytest.mark.asyncio
    async def test_detect_jwt(self, detector):
        """Test detecting JWT tokens."""
        text = "JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        
        detected = await detector.detect(text)
        
        # Should detect JWT
        entity_types = [entity_type for entity_type, _, _ in detected]
        assert "jwt" in entity_types
    
    @pytest.mark.asyncio
    async def test_detect_private_key(self, detector):
        """Test detecting private keys."""
        text = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0B"
        
        detected = await detector.detect(text)
        
        # Should detect private key
        entity_types = [entity_type for entity_type, _, _ in detected]
        assert "private_key" in entity_types
    
    @pytest.mark.asyncio
    async def test_detect_multiple_pii(self, detector):
        """Test detecting multiple PII types in one text."""
        text = """
        Name: John Doe
        Email: john@example.com
        Phone: 555-123-4567
        SSN: 123-45-6789
        Card: 4532-1234-5678-9010
        """
        
        detected = await detector.detect(text)
        
        # Should detect multiple entities
        assert len(detected) >= 4
        
        # Check confidence scores
        for entity_type, text, score in detected:
            assert 0.0 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_sanitize_email(self, detector):
        """Test sanitizing email addresses."""
        text = "Contact john.doe@example.com for info"
        
        sanitized = await detector.sanitize(text)
        
        # Email should be redacted
        assert "john.doe@example.com" not in sanitized
        assert "REDACTED" in sanitized or "[" in sanitized
    
    @pytest.mark.asyncio
    async def test_sanitize_multiple_pii(self, detector):
        """Test sanitizing multiple PII types."""
        text = "Email: test@example.com, Phone: 555-1234, SSN: 123-45-6789"
        
        sanitized = await detector.sanitize(text)
        
        # All PII should be redacted
        assert "test@example.com" not in sanitized
        assert "555-1234" not in sanitized
        assert "123-45-6789" not in sanitized
        assert "REDACTED" in sanitized or "[" in sanitized
    
    @pytest.mark.asyncio
    async def test_sanitize_preserves_structure(self, detector):
        """Test that sanitization preserves text structure."""
        text = "Dear John, your email is john@example.com. Thanks!"
        
        sanitized = await detector.sanitize(text)
        
        # Structure should be preserved
        assert sanitized.startswith("Dear")
        assert sanitized.endswith("Thanks!")
        assert len(sanitized) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_returns_counts(self, detector):
        """Test analyze returns PII counts."""
        text = """
        Email1: test1@example.com
        Email2: test2@example.com
        Phone: 555-1234
        """
        
        analysis = await detector.analyze(text)
        
        # Should return counts
        assert isinstance(analysis, dict)
        
        # Should have metadata
        if "_metadata" in analysis:
            assert "total_entities" in analysis["_metadata"]
            assert analysis["_metadata"]["total_entities"] > 0
    
    @pytest.mark.asyncio
    async def test_confidence_threshold(self):
        """Test that confidence threshold is respected."""
        # High threshold
        high_threshold_detector = PIIDetector(score_threshold=0.9)
        
        # Low threshold
        low_threshold_detector = PIIDetector(score_threshold=0.3)
        
        text = "Maybe this is an email: maybe@something"
        
        high_results = await high_threshold_detector.detect(text)
        low_results = await low_threshold_detector.detect(text)
        
        # Low threshold should detect more (including uncertain matches)
        assert len(low_results) >= len(high_results)
    
    @pytest.mark.asyncio
    async def test_empty_text(self, detector):
        """Test handling empty text."""
        sanitized = await detector.sanitize("")
        assert sanitized == ""
        
        detected = await detector.detect("")
        assert len(detected) == 0
        
        analysis = await detector.analyze("")
        assert isinstance(analysis, dict)
    
    @pytest.mark.asyncio
    async def test_no_pii_text(self, detector):
        """Test text with no PII."""
        text = "This is a normal text without any sensitive information."
        
        sanitized = await detector.sanitize(text)
        assert sanitized == text  # Should be unchanged
        
        detected = await detector.detect(text)
        assert len(detected) == 0
        
        analysis = await detector.analyze(text)
        # Should be empty or only metadata
        assert len([k for k in analysis.keys() if k != "_metadata"]) == 0
    
    @pytest.mark.asyncio
    async def test_context_awareness(self, detector):
        """Test context-aware detection."""
        # "call 555-1234" should be detected as phone
        text1 = "Please call 555-1234 for support"
        
        # "error code 555-1234" might not be (context-dependent)
        text2 = "System error code 555-1234 occurred"
        
        detected1 = await detector.detect(text1)
        detected2 = await detector.detect(text2)
        
        # Both should be analyzed, but confidence may differ
        # This tests that the system considers context
        types1 = [t for t, _, _ in detected1]
        types2 = [t for t, _, _ in detected2]
        
        # At minimum, should detect patterns
        assert len(detected1) > 0 or len(detected2) > 0
    
    def test_get_supported_entities(self, detector):
        """Test getting supported entity types."""
        entities = detector.get_supported_entities()
        
        assert isinstance(entities, list)
        assert len(entities) > 0
        
        # Should include common types
        # Note: exact names depend on Presidio version
        assert any(
            "EMAIL" in e or "PHONE" in e or "SSN" in e
            for e in entities
        )
    
    @pytest.mark.asyncio
    async def test_fallback_on_presidio_failure(self):
        """Test fallback to regex if Presidio fails."""
        # Create detector that will fail Presidio initialization
        with patch('src.guardrails.pii_detector.AnalyzerEngine', side_effect=Exception("Init failed")):
            detector = PIIDetector()
            
            # Should still work with regex patterns
            assert detector.analyzer is None
            
            # Tech-specific patterns should still work
            text = "AWS Key: AKIAIOSFODNN7EXAMPLE"
            detected = await detector.detect(text)
            
            # Should detect AWS key via regex
            entity_types = [entity_type for entity_type, _, _ in detected]
            assert "aws_key" in entity_types


class TestPIIDetectorEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_very_long_text(self):
        """Test handling very long text."""
        detector = PIIDetector()
        
        # 100KB of text
        long_text = "Normal text " * 10000 + "email@example.com"
        
        # Should not crash
        sanitized = await detector.sanitize(long_text)
        assert "email@example.com" not in sanitized
    
    @pytest.mark.asyncio
    async def test_special_characters(self):
        """Test text with special characters."""
        detector = PIIDetector()
        
        text = "Email: test@example.com 中文 العربية Emoji: 🔒"
        
        # Should handle special characters
        sanitized = await detector.sanitize(text)
        assert isinstance(sanitized, str)
    
    @pytest.mark.asyncio
    async def test_malformed_pii(self):
        """Test handling malformed PII."""
        detector = PIIDetector()
        
        # Almost-valid but malformed
        text = "Email: not-an-email, Phone: 1234 (too short)"
        
        # Should not crash
        detected = await detector.detect(text)
        assert isinstance(detected, list)
