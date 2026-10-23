"""
Usage Tracker for Metered Billing

Tracks token usage and compression savings for billing purposes.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class UsageTracker:
    """
    Tracks usage metrics for metered billing.
    
    Metrics tracked:
    - Tokens saved through compression
    - Compression ratios
    - Request counts
    - Cache hit rates
    """
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
    
    async def track_request(
        self,
        tenant_id: str,
        tokens_saved: int,
        compression_ratio: float,
        cache_hits: int = 0
    ) -> None:
        """
        Track a single request for billing.
        
        Args:
            tenant_id: Tenant identifier
            tokens_saved: Number of tokens saved by compression
            compression_ratio: Compression ratio (0-1)
            cache_hits: Number of cache hits
        """
        try:
            # Increment usage counters in Redis
            usage_key = f"usage:{tenant_id}"
            
            await self.redis_client.hincrby(usage_key, "tokens_saved", tokens_saved)
            await self.redis_client.hincrby(usage_key, "requests", 1)
            await self.redis_client.hincrby(usage_key, "cache_hits", cache_hits)
            
            # Store latest compression ratio (for analytics)
            await self.redis_client.set(
                f"usage:{tenant_id}:last_compression",
                str(compression_ratio),
                ex=3600
            )
            
            logger.debug(
                f"Tracked usage for {tenant_id}: "
                f"{tokens_saved} tokens saved, "
                f"{compression_ratio:.2%} compression"
            )
            
        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
    
    async def get_usage(self, tenant_id: str) -> dict:
        """
        Get current usage for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dictionary with usage metrics
        """
        try:
            usage_key = f"usage:{tenant_id}"
            usage_data = await self.redis_client.hgetall(usage_key)
            
            return {
                "tokens_saved": int(usage_data.get("tokens_saved", 0)),
                "requests": int(usage_data.get("requests", 0)),
                "cache_hits": int(usage_data.get("cache_hits", 0)),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting usage: {e}")
            return {}
    
    async def reset_usage(self, tenant_id: str) -> bool:
        """
        Reset usage counters (called after billing sync).
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            True if successful
        """
        try:
            usage_key = f"usage:{tenant_id}"
            await self.redis_client.delete(usage_key)
            logger.info(f"Reset usage for {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting usage: {e}")
            return False
