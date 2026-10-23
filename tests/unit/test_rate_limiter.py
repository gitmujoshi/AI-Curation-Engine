"""
Unit Tests for Rate Limiter

Tests the Redis-based rate limiting system.
"""

import pytest
import time
from unittest.mock import Mock, AsyncMock, patch

from src.gateway.rate_limiter import (
    RateLimiter,
    AdaptiveRateLimiter,
    RateLimitConfig,
    RateLimitResult
)


@pytest.fixture
async def mock_redis():
    """Create mock Redis client."""
    redis = AsyncMock()
    
    # Mock eval to return allowed=True by default
    redis.eval.return_value = [1, 99, int(time.time()) + 60]
    
    # Mock other methods
    redis.zadd = AsyncMock()
    redis.expire = AsyncMock()
    redis.delete = AsyncMock()
    redis.zremrangebyscore = AsyncMock()
    redis.zcard = AsyncMock(return_value=0)
    redis.get = AsyncMock(return_value=None)
    
    return redis


@pytest.fixture
def rate_limiter(mock_redis):
    """Create rate limiter instance."""
    return RateLimiter(mock_redis)


@pytest.fixture
def adaptive_limiter(mock_redis):
    """Create adaptive rate limiter instance."""
    return AdaptiveRateLimiter(mock_redis)


class TestRateLimitConfig:
    """Test RateLimitConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        
        assert config.requests_per_minute == 100
        assert config.requests_per_hour == 1000
        assert config.requests_per_day == 10000
        assert config.burst_size == 20
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = RateLimitConfig(
            requests_per_minute=50,
            requests_per_hour=500,
            requests_per_day=5000,
            burst_size=10
        )
        
        assert config.requests_per_minute == 50
        assert config.requests_per_hour == 500


class TestRateLimiter:
    """Test RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self, rate_limiter, mock_redis):
        """Test rate limit check when allowed."""
        # Mock Redis to return allowed
        mock_redis.eval.return_value = [1, 50, int(time.time()) + 60]
        
        config = RateLimitConfig(requests_per_minute=100)
        result = await rate_limiter.check_rate_limit("tenant_123", config)
        
        assert result.allowed is True
        assert result.remaining == 50
        assert result.retry_after is None
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_denied(self, rate_limiter, mock_redis):
        """Test rate limit check when denied."""
        current_time = int(time.time())
        reset_at = current_time + 30
        
        # Mock Redis to return denied
        mock_redis.eval.return_value = [0, 0, reset_at]
        
        config = RateLimitConfig(requests_per_minute=100)
        result = await rate_limiter.check_rate_limit("tenant_123", config)
        
        assert result.allowed is False
        assert result.remaining == 0
        assert result.retry_after == 30
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_multiple_windows(self, rate_limiter, mock_redis):
        """Test rate limit checks all time windows."""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000
        )
        
        await rate_limiter.check_rate_limit("tenant_123", config)
        
        # Should have called eval 3 times (minute, hour, day)
        assert mock_redis.eval.call_count == 3
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_stops_at_first_deny(self, rate_limiter, mock_redis):
        """Test that checking stops at first denial."""
        # First window (minute) denies
        mock_redis.eval.return_value = [0, 0, int(time.time()) + 60]
        
        config = RateLimitConfig()
        result = await rate_limiter.check_rate_limit("tenant_123", config)
        
        assert result.allowed is False
        # Should only call eval once (stopped at minute window)
        assert mock_redis.eval.call_count == 1
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_redis_failure(self, rate_limiter, mock_redis):
        """Test rate limit fails open on Redis errors."""
        # Mock Redis to raise exception
        mock_redis.eval.side_effect = Exception("Redis connection failed")
        
        config = RateLimitConfig()
        result = await rate_limiter.check_rate_limit("tenant_123", config)
        
        # Should fail open (allow request)
        assert result.allowed is True
    
    @pytest.mark.asyncio
    async def test_increment_counter(self, rate_limiter, mock_redis):
        """Test manually incrementing rate limit counter."""
        await rate_limiter.increment("tenant_123", amount=5)
        
        # Should have called zadd for each window
        assert mock_redis.zadd.call_count == 15  # 3 windows * 5 increments
        assert mock_redis.expire.call_count == 3
    
    @pytest.mark.asyncio
    async def test_reset_limits(self, rate_limiter, mock_redis):
        """Test resetting rate limits."""
        await rate_limiter.reset("tenant_123")
        
        # Should delete all window keys
        assert mock_redis.delete.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_current_usage(self, rate_limiter, mock_redis):
        """Test getting current usage."""
        # Mock Redis to return counts
        mock_redis.zcard.side_effect = [10, 100, 500]
        
        usage = await rate_limiter.get_current_usage("tenant_123")
        
        assert usage["minute"] == 10
        assert usage["hour"] == 100
        assert usage["day"] == 500


class TestAdaptiveRateLimiter:
    """Test AdaptiveRateLimiter class."""
    
    def test_tier_configs_exist(self, adaptive_limiter):
        """Test that tier configurations are defined."""
        assert "free" in adaptive_limiter.TIER_CONFIGS
        assert "growth" in adaptive_limiter.TIER_CONFIGS
        assert "business" in adaptive_limiter.TIER_CONFIGS
        assert "enterprise" in adaptive_limiter.TIER_CONFIGS
    
    def test_tier_configs_hierarchy(self, adaptive_limiter):
        """Test that higher tiers have higher limits."""
        free = adaptive_limiter.TIER_CONFIGS["free"]
        growth = adaptive_limiter.TIER_CONFIGS["growth"]
        business = adaptive_limiter.TIER_CONFIGS["business"]
        enterprise = adaptive_limiter.TIER_CONFIGS["enterprise"]
        
        # Check minute limits
        assert free.requests_per_minute < growth.requests_per_minute
        assert growth.requests_per_minute < business.requests_per_minute
        assert business.requests_per_minute < enterprise.requests_per_minute
        
        # Check hour limits
        assert free.requests_per_hour < growth.requests_per_hour
        assert growth.requests_per_hour < business.requests_per_hour
        
        # Check day limits
        assert free.requests_per_day < enterprise.requests_per_day
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_for_tier_free(self, adaptive_limiter, mock_redis):
        """Test rate limit check for free tier."""
        mock_redis.eval.return_value = [1, 5, int(time.time()) + 60]
        
        result = await adaptive_limiter.check_rate_limit_for_tier(
            "tenant_123",
            "free"
        )
        
        assert result.allowed is True
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_for_tier_enterprise(self, adaptive_limiter, mock_redis):
        """Test rate limit check for enterprise tier."""
        mock_redis.eval.return_value = [1, 500, int(time.time()) + 60]
        
        result = await adaptive_limiter.check_rate_limit_for_tier(
            "tenant_123",
            "enterprise"
        )
        
        assert result.allowed is True
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_for_invalid_tier(self, adaptive_limiter, mock_redis):
        """Test rate limit with invalid tier defaults to free."""
        mock_redis.eval.return_value = [1, 5, int(time.time()) + 60]
        
        result = await adaptive_limiter.check_rate_limit_for_tier(
            "tenant_123",
            "invalid_tier"
        )
        
        # Should default to free tier
        assert result.allowed is True
    
    @pytest.mark.asyncio
    async def test_check_abuse_pattern_no_abuse(self, adaptive_limiter, mock_redis):
        """Test abuse pattern check when no abuse detected."""
        # Mock Redis to return normal values
        mock_redis.get.return_value = None
        mock_redis.zcard.return_value = 50
        
        is_abuse, reason = await adaptive_limiter.check_abuse_pattern("tenant_123")
        
        assert is_abuse is False
        assert reason is None
    
    @pytest.mark.asyncio
    async def test_check_abuse_pattern_too_many_failures(self, adaptive_limiter, mock_redis):
        """Test abuse pattern detection for too many failures."""
        # Mock Redis to return high failure count
        mock_redis.get.return_value = "15"
        
        is_abuse, reason = await adaptive_limiter.check_abuse_pattern("tenant_123")
        
        assert is_abuse is True
        assert "failed" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_check_abuse_pattern_sustained_max_rate(self, adaptive_limiter, mock_redis):
        """Test abuse pattern detection for sustained max rate."""
        # Mock Redis to return high current usage and previous usage
        def get_side_effect(key):
            if "minute_ago" in key:
                return "950"
            return None
        
        mock_redis.get.side_effect = get_side_effect
        mock_redis.zcard.return_value = 950
        
        is_abuse, reason = await adaptive_limiter.check_abuse_pattern("tenant_123")
        
        assert is_abuse is True
        assert "rate" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_check_abuse_pattern_redis_failure(self, adaptive_limiter, mock_redis):
        """Test abuse pattern check fails safe on Redis errors."""
        # Mock Redis to raise exception
        mock_redis.get.side_effect = Exception("Redis error")
        
        is_abuse, reason = await adaptive_limiter.check_abuse_pattern("tenant_123")
        
        # Should fail safe (no abuse)
        assert is_abuse is False


class TestRateLimitHeaders:
    """Test rate limit HTTP headers."""
    
    def test_rate_limit_result_structure(self):
        """Test RateLimitResult has correct fields."""
        result = RateLimitResult(
            allowed=True,
            limit=100,
            remaining=50,
            reset_at=1234567890
        )
        
        assert result.allowed is True
        assert result.limit == 100
        assert result.remaining == 50
        assert result.reset_at == 1234567890
        assert result.retry_after is None
    
    def test_rate_limit_result_with_retry_after(self):
        """Test RateLimitResult with retry_after."""
        result = RateLimitResult(
            allowed=False,
            limit=100,
            remaining=0,
            reset_at=1234567890,
            retry_after=30
        )
        
        assert result.allowed is False
        assert result.retry_after == 30


class TestRateLimitScenarios:
    """Test real-world rate limiting scenarios."""
    
    @pytest.mark.asyncio
    async def test_burst_traffic_handling(self, rate_limiter, mock_redis):
        """Test handling burst traffic."""
        config = RateLimitConfig(
            requests_per_minute=10,
            burst_size=5
        )
        
        # Simulate 15 rapid requests
        results = []
        for i in range(15):
            # First 10 allowed, rest denied
            if i < 10:
                mock_redis.eval.return_value = [1, 10-i-1, int(time.time()) + 60]
            else:
                mock_redis.eval.return_value = [0, 0, int(time.time()) + 60]
            
            result = await rate_limiter.check_rate_limit("tenant_123", config)
            results.append(result.allowed)
        
        # Some should be allowed, some denied
        assert any(results)  # At least some allowed
        assert not all(results)  # Not all allowed
    
    @pytest.mark.asyncio
    async def test_different_tenants_independent_limits(self, rate_limiter, mock_redis):
        """Test that different tenants have independent limits."""
        config = RateLimitConfig(requests_per_minute=10)
        
        # Tenant 1 hits limit
        mock_redis.eval.return_value = [0, 0, int(time.time()) + 60]
        result1 = await rate_limiter.check_rate_limit("tenant_1", config)
        
        # Tenant 2 should still be allowed
        mock_redis.eval.return_value = [1, 9, int(time.time()) + 60]
        result2 = await rate_limiter.check_rate_limit("tenant_2", config)
        
        assert result1.allowed is False
        assert result2.allowed is True
    
    @pytest.mark.asyncio
    async def test_limit_resets_after_window(self, rate_limiter, mock_redis):
        """Test that limits reset after time window."""
        config = RateLimitConfig(requests_per_minute=10)
        
        # First request at time T
        mock_redis.eval.return_value = [1, 9, int(time.time()) + 60]
        result1 = await rate_limiter.check_rate_limit("tenant_123", config)
        
        # After window expires, should be allowed again
        # (In real implementation, old entries are removed by Lua script)
        mock_redis.eval.return_value = [1, 9, int(time.time()) + 60]
        result2 = await rate_limiter.check_rate_limit("tenant_123", config)
        
        assert result1.allowed is True
        assert result2.allowed is True
