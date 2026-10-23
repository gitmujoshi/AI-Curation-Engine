"""
Headroom Content Router

Analyzes payload content type and routes to appropriate compression engine.
"""

import json
import logging
import re
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content type classification."""
    CODE = "code"
    JSON = "json"
    PROSE = "prose"
    MIXED = "mixed"


class ContentRouter:
    """
    Routes content to appropriate compression strategy based on type analysis.
    """
    
    CODE_PATTERNS = [
        r'def\s+\w+\s*\(',
        r'function\s+\w+\s*\(',
        r'class\s+\w+',
        r'import\s+\w+',
        r'from\s+\w+\s+import',
        r'=>',
        r'const\s+\w+',
        r'let\s+\w+',
    ]
    
    def __init__(self):
        self.code_regex = re.compile('|'.join(self.CODE_PATTERNS))
    
    def classify_content(self, content: str) -> ContentType:
        """
        Classify content type for optimal compression routing.
        
        Args:
            content: Text content to classify
            
        Returns:
            ContentType enum value
        """
        # Try to parse as JSON
        try:
            json.loads(content)
            return ContentType.JSON
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Check for code patterns
        if self.code_regex.search(content):
            return ContentType.CODE
        
        # Default to prose
        return ContentType.PROSE
    
    async def route_and_compress(
        self,
        messages: List[Dict[str, Any]],
        compressor: 'HeadroomCompressor'
    ) -> List[Dict[str, Any]]:
        """
        Route messages to appropriate compression strategy.
        
        Args:
            messages: List of chat messages
            compressor: HeadroomCompressor instance
            
        Returns:
            Compressed messages
        """
        compressed_messages = []
        
        for msg in messages:
            content = msg.get("content", "")
            
            # Skip system messages (usually short)
            if msg.get("role") == "system":
                compressed_messages.append(msg)
                continue
            
            # Classify and compress
            content_type = self.classify_content(content)
            
            if content_type == ContentType.CODE:
                compressed_content = await compressor.compress_code(content)
            elif content_type == ContentType.JSON:
                compressed_content = await compressor.compress_json(content)
            else:
                compressed_content = await compressor.compress_prose(content)
            
            compressed_msg = {
                **msg,
                "content": compressed_content
            }
            compressed_messages.append(compressed_msg)
        
        logger.info(f"Routed and compressed {len(messages)} messages")
        return compressed_messages
