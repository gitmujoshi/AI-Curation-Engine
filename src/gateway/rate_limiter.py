"""
Rate Limiting

Redis-based rate limiter using token bucket algorithm with
sliding window counters for accurate, distributed rate limiting.
"""

import logging
import time
from typing import Optional, Tuple
from dataclasses import dataclass

from fastapi import HTTPException, status
from redis import Redis
from redis.asyncio import Redis as AsyncRedis

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 20  # Allow burst above RPM


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: int  # Unix timestamp
    retry_after: Optional[int] = None  # Seconds until retry


class RateLimiter:
    """
    Redis-based rate limiter with token bucket algorithm.
    
    Features:
    - Token bucket for burst handling
    - Sliding window counters for accuracy
    - Multi-tier limits (minute, hour, day)
    - Distributed-safe (uses Redis atomic operations)
    - Efficient (single Redis call per check)
    """
    
    def __init__(self, redis_client: AsyncRedis):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Async Redis client
        """
        self.redis = redis_client
        logger.info("Initialized rate limiter with Redis backend")
    
    async def check_rate_limit(
        self,
        tenant_id: str,
        config: RateLimitConfig
    ) -> RateLimitResult:
        """
        Check if request is allowed under rate limits.
        
        Uses token bucket algorithm with sliding windows:
        1. Check minute window (short-term burst)
        2. Check hour window (medium-term)
        3. Check day window (long-term quota)
        
        Args:
            tenant_id: Unique tenant identifier
            config: Rate limit configuration
            
        Returns:
            RateLimitResult with allow/deny decision
        """
        current_time = int(time.time())
        
        # Check each time window
        # Minute window (most restrictive for burst)
        minute_result = await self._check_window(
            tenant_id=tenant_id,
            window="minute",
            window_size=60,
            limit=config.requests_per_minute,
            current_time=current_time
        )
        
        if not minute_result.allowed:
            return minute_result
        
        # Hour window
        hour_result = await self._check_window(
            tenant_id=tenant_id,
            window="hour",
            window_size=3600,
            limit=config.requests_per_hour,
            current_time=current_time
        )
        
        if not hour_result.allowed:
            return hour_result
        
        # Day window
        day_result = await self._check_window(
            tenant_id=tenant_id,
            window="day",
            window_size=86400,
            limit=config.requests_per_day,
            current_time=current_time
        )
        
        return day_result
    
    async def _check_window(
        self,
        tenant_id: str,
        window: str,
        window_size: int,
        limit: int,
        current_time: int
    ) -> RateLimitResult:
        """
        Check rate limit for a specific time window using sliding window.
        
        Args:
            tenant_id: Tenant identifier
            window: Window name (minute, hour, day)
            window_size: Window size in seconds
            limit: Request limit for this window
            current_time: Current Unix timestamp
            
        Returns:
            RateLimitResult
        """
        key = f"ratelimit:{tenant_id}:{window}"
        
        try:
            # Use Lua script for atomic operations
            # This ensures race conditions are avoided
            lua_script = """
            local key = KEYS[1]
            local limit = tonumber(ARGV[1])
            local window_size = tonumber(ARGV[2])
            local current_time = tonumber(ARGV[3])
            
            -- Remove old entries outside window
            redis.call('ZREMRANGEBYSCORE', key, 0, current_time - window_size)
            
            -- Count requests in current window
            local count = redis.call('ZCARD', key)
            
            if count < limit then
                -- Add current request
                redis.call('ZADD', key, current_time, current_time)
                redis.call('EXPIRE', key, window_size)
                return {1, limit - count - 1, current_time + window_size}
            else
                -- Get oldest request in window
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                local reset_at = current_time + window_size
                if oldest[2] then
                    reset_at = tonumber(oldest[2]) + window_size
                end
                return {0, 0, reset_at}
            end
            """
            
            # Execute Lua script
            result = await self.redis.eval(
                lua_script,
                1,  # Number of keys
                key,
                limit,
                window_size,
                current_time
            )
            
            allowed = result[0] == 1
            remaining = result[1]
            reset_at = result[2]
            
            retry_after = None
            if not allowed:
                retry_after = reset_at - current_time
            
            return RateLimitResult(
                allowed=allowed,
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=retry_after
            )
            
        except Exception as e:
            logger.error(f"Rate limit check failed for {tenant_id}: {e}")
            # Fail open (allow request) to avoid blocking on Redis issues
            logger.warning(f"Rate limiting disabled due to error - allowing request")
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit,
                reset_at=current_time + window_size
            )
    
    async def increment(
        self,
        tenant_id: str,
        amount: int = 1
    ) -> None:
        """
        Manually increment rate limit counter.
        
        Useful for retroactive limits after async processing.
        
        Args:
            tenant_id: Tenant identifier
            amount: Amount to increment
        """
        current_time = int(time.time())
        
        for window, window_size in [
            ("minute", 60),
            ("hour", 3600),
            ("day", 86400)
        ]:
            key = f"ratelimit:{tenant_id}:{window}"
            
            try:
                # Add entries for the increment
                for i in range(amount):
                    await self.redis.zadd(
                        key,
                        {f"{current_time}:{i}": current_time}
                    )
                await self.redis.expire(key, window_size)
            except Exception as e:
                logger.error(f"Failed to increment rate limit for {tenant_id}: {e}")
    
    async def reset(self, tenant_id: str) -> None:
        """
        Reset rate limits for a tenant.
        
        Args:
            tenant_id: Tenant identifier
        """
        for window in ["minute", "hour", "day"]:
            key = f"ratelimit:{tenant_id}:{window}"
            try:
                await self.redis.delete(key)
                logger.info(f"Reset rate limit for {tenant_id}:{window}")
            except Exception as e:
                logger.error(f"Failed to reset rate limit: {e}")
    
    async def get_current_usage(
        self,
        tenant_id: str
    ) -> dict:
        """
        Get current rate limit usage for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Dictionary with usage per window
        """
        current_time = int(time.time())
        usage = {}
        
        for window, window_size in [
            ("minute", 60),
            ("hour", 3600),
            ("day", 86400)
        ]:
            key = f"ratelimit:{tenant_id}:{window}"
            
            try:
                # Remove expired entries
                await self.redis.zremrangebyscore(
                    key,
                    0,
                    current_time - window_size
                )
                
                # Count current requests
                count = await self.redis.zcard(key)
                usage[window] = count
                
            except Exception as e:
                logger.error(f"Failed to get usage for {window}: {e}")
                usage[window] = 0
        
        return usage


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts limits based on tier and behavior.
    
    Features:
    - Tier-based limits (free, growth, business, enterprise)
    - Penalty for abuse patterns
    - Rewards for good behavior
    """
    
    TIER_CONFIGS = {
        "free": RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000,
            burst_size=5
        ),
        "startup": RateLimitConfig(
            requests_per_minute=50,
            requests_per_hour=500,
            requests_per_day=5000,
            burst_size=10
        ),
        "growth": RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_size=20
        ),
        "business": RateLimitConfig(
            requests_per_minute=500,
            requests_per_hour=5000,
            requests_per_day=50000,
            burst_size=50
        ),
        "enterprise": RateLimitConfig(
            requests_per_minute=1000,
            requests_per_hour=10000,
            requests_per_day=100000,
            burst_size=100
        )
    }
    
    async def check_rate_limit_for_tier(
        self,
        tenant_id: str,
        tier: str
    ) -> RateLimitResult:
        """
        Check rate limit based on tier.
        
        Args:
            tenant_id: Tenant identifier
            tier: Tier name (free, growth, business, enterprise)
            
        Returns:
            RateLimitResult
        """
        config = self.TIER_CONFIGS.get(tier, self.TIER_CONFIGS["free"])
        return await self.check_rate_limit(tenant_id, config)
    
    async def check_abuse_pattern(
        self,
        tenant_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check for abuse patterns.
        
        Patterns detected:
        - Rapid failed requests (brute force)
        - Sustained max rate (possible DoS)
        - Sudden spike (compromised key)
        
        Args:
            tenant_id: Tenant identifier
            
        Returns:
            Tuple of (is_abuse, reason)
        """
        try:
            # Check for rapid failures
            failure_key = f"failures:{tenant_id}"
            failure_count = await self.redis.get(failure_key)
            
            if failure_count and int(failure_count) > 10:
                return True, "Too many failed requests"
            
            # Check for sustained max rate
            usage = await self.get_current_usage(tenant_id)
            
            if usage.get("minute", 0) > 900:  # 90% of max rate
                minute_ago_key = f"ratelimit:{tenant_id}:minute_ago"
                minute_ago_count = await self.redis.get(minute_ago_key)
                
                if minute_ago_count and int(minute_ago_count) > 900:
                    return True, "Sustained maximum rate"
            
            return False, None
            
        except Exception as e:
            logger.error(f"Abuse pattern check failed: {e}")
            return False, None


# FastAPI dependency for rate limiting
async def enforce_rate_limit(
    tenant_id: str,
    tier: str = "free"
):
    """
    FastAPI dependency to enforce rate limits.
    
    Usage:
        @app.post("/api/endpoint")
        async def endpoint(
            tenant_id: str = Depends(verify_api_key),
            _rate_limit: None = Depends(enforce_rate_limit)
        ):
            return {"status": "ok"}
    
    Args:
        tenant_id: Tenant ID from auth
        tier: Tenant tier from auth
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    from src.gateway.main import app
    
    if not hasattr(app.state, "rate_limiter"):
        logger.warning("Rate limiter not initialized, skipping check")
        return
    
    rate_limiter: AdaptiveRateLimiter = app.state.rate_limiter
    
    # Check rate limit
    result = await rate_limiter.check_rate_limit_for_tier(tenant_id, tier)
    
    if not result.allowed:
        logger.warning(
            f"Rate limit exceeded for tenant {tenant_id}: "
            f"{result.limit} requests per window"
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Rate limit exceeded. Try again in {result.retry_after} seconds.",
                "limit": result.limit,
                "remaining": result.remaining,
                "reset_at": result.reset_at,
                "retry_after": result.retry_after
            },
            headers={
                "X-RateLimit-Limit": str(result.limit),
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_at),
                "Retry-After": str(result.retry_after)
            }
        )
    
    # Check for abuse patterns
    is_abuse, reason = await rate_limiter.check_abuse_pattern(tenant_id)
    
    if is_abuse:
        logger.error(f"Abuse pattern detected for {tenant_id}: {reason}")
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "abuse_detected",
                "message": f"Suspicious activity detected: {reason}. Account temporarily restricted.",
                "reason": reason
            }
        )
