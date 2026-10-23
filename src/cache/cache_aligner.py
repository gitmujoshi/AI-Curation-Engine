"""
Cache Aligner - Prefix Optimization

Optimizes prompt structure for LLM provider KV cache hits.
"""

import logging
from typing import Any, Dict, List
import hashlib

logger = logging.getLogger(__name__)


class CacheAligner:
    """
    Optimizes prompt structure for maximum KV cache hits.
    
    Strategy:
    1. Move dynamic attributes (UUIDs, timestamps) to end of prompt
    2. Ensure static content appears first
    3. Group similar content together
    """
    
    DYNAMIC_PATTERNS = [
        "timestamp",
        "uuid",
        "session_id",
        "request_id",
        "user_id",
        "date",
        "time"
    ]
    
    async def optimize_for_kv_cache(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Optimize message ordering for KV cache efficiency.
        
        Args:
            messages: List of chat messages
            
        Returns:
            Reordered messages optimized for cache hits
        """
        optimized = []
        
        for msg in messages:
            content = msg.get("content", "")
            
            # Extract dynamic attributes
            static_parts = []
            dynamic_parts = []
            
            lines = content.split("\n")
            for line in lines:
                is_dynamic = any(pattern in line.lower() for pattern in self.DYNAMIC_PATTERNS)
                
                if is_dynamic:
                    dynamic_parts.append(line)
                else:
                    static_parts.append(line)
            
            # Reconstruct: static first, dynamic last
            if static_parts or dynamic_parts:
                optimized_content = "\n".join(static_parts)
                if dynamic_parts:
                    optimized_content += "\n\n--- Dynamic Attributes ---\n"
                    optimized_content += "\n".join(dynamic_parts)
                
                optimized_msg = {
                    **msg,
                    "content": optimized_content
                }
            else:
                optimized_msg = msg
            
            optimized.append(optimized_msg)
        
        logger.debug(f"Optimized {len(messages)} messages for KV cache")
        return optimized
    
    def calculate_cache_key(self, messages: List[Dict[str, Any]]) -> str:
        """
        Calculate cache key for message sequence.
        
        Args:
            messages: List of messages
            
        Returns:
            SHA-256 hash of static content
        """
        # Extract only static content for cache key
        static_content = []
        
        for msg in messages:
            if msg.get("role") == "system":
                static_content.append(msg.get("content", ""))
        
        combined = "\n".join(static_content)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
