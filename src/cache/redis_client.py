"""
Redis Client for Caching

High-performance Redis client with connection pooling.
"""

import logging
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from src.gateway.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client with connection pooling.
    
    Used for:
    - Headroom content caching
    - API key validation cache
    - Usage tracking
    - Rate limiting
    """
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.pool: Optional[ConnectionPool] = None
        self.client: Optional[aioredis.Redis] = None
    
    async def connect(self) -> None:
        """Initialize Redis connection pool."""
        try:
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                decode_responses=True
            )
            self.client = aioredis.Redis(connection_pool=self.pool)
            
            # Test connection
            await self.client.ping()
            logger.info("✅ Connected to Redis successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def close(self) -> None:
        """Close Redis connection pool."""
        if self.client:
            await self.client.close()
        if self.pool:
            await self.pool.disconnect()
        logger.info("Closed Redis connection")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None
    ) -> bool:
        """
        Set value in Redis.
        
        Args:
            key: Redis key
            value: Value to store
            ex: Expiration time in seconds
            
        Returns:
            True if successful
        """
        try:
            await self.client.set(key, value, ex=ex)
            return True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False
    
    async def incr(self, key: str) -> int:
        """Increment integer value."""
        try:
            return await self.client.incr(key)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            return 0
    
    async def hincrby(self, name: str, key: str, amount: int = 1) -> int:
        """Increment hash field by amount."""
        try:
            return await self.client.hincrby(name, key, amount)
        except Exception as e:
            logger.error(f"Error incrementing hash {name}:{key}: {e}")
            return 0
    
    async def hgetall(self, name: str) -> dict:
        """Get all fields from hash."""
        try:
            return await self.client.hgetall(name)
        except Exception as e:
            logger.error(f"Error getting hash {name}: {e}")
            return {}
    
    async def ping(self) -> bool:
        """Ping Redis to check connection."""
        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False
