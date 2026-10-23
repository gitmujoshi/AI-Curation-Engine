"""
Prompt Injection Detection

Detects malicious prompt injections and jailbreak attempts.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)


class PromptInjectionDetector:
    """
    Detects prompt injection attacks and jailbreak attempts.
    
    Detection strategies:
    1. Pattern matching for known attack vectors
    2. Structural analysis for prompt override attempts
    3. Instruction conflict detection
    """
    
    # Known malicious patterns
    MALICIOUS_PATTERNS = [
        # Direct instruction override
        r'ignore\s+(all\s+)?previous\s+instructions',
        r'disregard\s+(all\s+)?previous\s+instructions',
        r'forget\s+(all\s+)?previous\s+instructions',
        
        # System prompt extraction
        r'show\s+me\s+your\s+(system\s+)?prompt',
        r'what\s+are\s+your\s+instructions',
        r'repeat\s+your\s+instructions',
        
        # Role manipulation
        r'you\s+are\s+now\s+a',
        r'act\s+as\s+a',
        r'pretend\s+to\s+be',
        
        # Delimiter injection
        r'"""\s*\n\s*System:',
        r'</s>',
        r'\[INST\]',
        
        # Jailbreak attempts
        r'DAN\s+mode',
        r'developer\s+mode',
        r'god\s+mode',
    ]
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.MALICIOUS_PATTERNS]
        logger.info("Initialized prompt injection detector")
    
    async def detect(self, text: str) -> bool:
        """
        Detect if text contains prompt injection attempts.
        
        Args:
            text: User input to analyze
            
        Returns:
            True if injection detected, False otherwise
        """
        # Check against known patterns
        for pattern in self.patterns:
            if pattern.search(text):
                logger.warning(f"Detected prompt injection: matched pattern {pattern.pattern}")
                return True
        
        # Check for excessive special characters (delimiter injection)
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        if special_char_ratio > 0.3:
            logger.warning(f"Detected potential delimiter injection: {special_char_ratio:.2%} special chars")
            return True
        
        # Check for multiple system-like prefixes
        system_prefixes = ['system:', 'assistant:', 'user:', '[system]', '[assistant]']
        prefix_count = sum(1 for prefix in system_prefixes if prefix.lower() in text.lower())
        if prefix_count >= 3:
            logger.warning(f"Detected potential role manipulation: {prefix_count} system prefixes")
            return True
        
        return False
    
    async def analyze(self, text: str) -> dict:
        """
        Analyze text for injection indicators without binary decision.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with analysis results
        """
        matched_patterns = []
        for pattern in self.patterns:
            if pattern.search(text):
                matched_patterns.append(pattern.pattern)
        
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        
        system_prefixes = ['system:', 'assistant:', 'user:', '[system]', '[assistant]']
        prefix_count = sum(1 for prefix in system_prefixes if prefix.lower() in text.lower())
        
        return {
            "is_malicious": bool(matched_patterns) or special_char_ratio > 0.3 or prefix_count >= 3,
            "matched_patterns": matched_patterns,
            "special_char_ratio": special_char_ratio,
            "system_prefix_count": prefix_count,
            "risk_score": len(matched_patterns) * 0.4 + min(special_char_ratio * 2, 0.4) + min(prefix_count * 0.1, 0.2)
        }
