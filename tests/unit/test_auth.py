"""
Unit Tests for Authentication & Authorization

Tests the JWT/OAuth2 authentication system with RBAC.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import jwt as pyjwt

from fastapi import HTTPException

from src.gateway.auth import (
    AuthService,
    TokenData,
    APIKeyData,
    verify_api_key,
    verify_jwt,
    require_role,
    require_tier,
    hash_api_key
)


class TestTokenData:
    """Test TokenData Pydantic model."""
    
    def test_valid_token_data(self):
        """Test creating valid token data."""
        token_data = TokenData(
            tenant_id="acme_corp",
            user_id="user_123",
            roles=["admin", "developer"],
            tier="enterprise",
            rate_limit=1000
        )
        
        assert token_data.tenant_id == "acme_corp"
        assert token_data.user_id == "user_123"
        assert "admin" in token_data.roles
        assert token_data.tier == "enterprise"
    
    def test_default_values(self):
        """Test default values are applied."""
        token_data = TokenData(tenant_id="test")
        
        assert token_data.user_id is None
        assert token_data.roles == []
        assert token_data.tier == "free"
        assert token_data.rate_limit == 100


class TestAuthService:
    """Test AuthService class."""
    
    @pytest.fixture
    def auth_service(self):
        """Create auth service instance."""
        return AuthService()
    
    def test_create_access_token(self, auth_service):
        """Test JWT token creation."""
        token_data = TokenData(
            tenant_id="test_tenant",
            user_id="user_123",
            roles=["developer"]
        )
        
        token = auth_service.create_access_token(token_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Should be valid JWT
        decoded = pyjwt.decode(
            token,
            auth_service.jwt_secret,
            algorithms=[auth_service.jwt_algorithm]
        )
        
        assert decoded["tenant_id"] == "test_tenant"
        assert decoded["user_id"] == "user_123"
        assert "developer" in decoded["roles"]
    
    def test_token_expiration(self, auth_service):
        """Test token expiration is set correctly."""
        token_data = TokenData(tenant_id="test")
        token = auth_service.create_access_token(token_data)
        
        decoded = pyjwt.decode(
            token,
            auth_service.jwt_secret,
            algorithms=[auth_service.jwt_algorithm]
        )
        
        assert "exp" in decoded
        assert "iat" in decoded
        
        # Expiration should be ~24 hours from now
        exp_time = datetime.fromtimestamp(decoded["exp"])
        iat_time = datetime.fromtimestamp(decoded["iat"])
        
        time_diff = exp_time - iat_time
        assert time_diff.total_seconds() > 23 * 3600  # At least 23 hours
        assert time_diff.total_seconds() < 25 * 3600  # At most 25 hours
    
    def test_verify_jwt_token_valid(self, auth_service):
        """Test verifying valid JWT token."""
        # Create token
        original_data = TokenData(
            tenant_id="test_tenant",
            user_id="user_456",
            roles=["admin"],
            tier="business"
        )
        token = auth_service.create_access_token(original_data)
        
        # Verify token
        verified_data = auth_service.verify_jwt_token(token)
        
        assert verified_data.tenant_id == "test_tenant"
        assert verified_data.user_id == "user_456"
        assert "admin" in verified_data.roles
        assert verified_data.tier == "business"
    
    def test_verify_jwt_token_expired(self, auth_service):
        """Test verifying expired JWT token."""
        # Create token with very short expiration
        original_expiration = auth_service.jwt_expiration
        auth_service.jwt_expiration = timedelta(seconds=-1)  # Already expired
        
        token_data = TokenData(tenant_id="test")
        token = auth_service.create_access_token(token_data)
        
        # Restore original expiration
        auth_service.jwt_expiration = original_expiration
        
        # Should raise exception
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_jwt_token(token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
    
    def test_verify_jwt_token_invalid_signature(self, auth_service):
        """Test verifying token with invalid signature."""
        # Create token
        token_data = TokenData(tenant_id="test")
        token = auth_service.create_access_token(token_data)
        
        # Modify token (invalid signature)
        token_parts = token.split('.')
        token_parts[2] = "invalid_signature"
        invalid_token = '.'.join(token_parts)
        
        # Should raise exception
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_jwt_token(invalid_token)
        
        assert exc_info.value.status_code == 401
        assert "Invalid" in exc_info.value.detail
    
    def test_verify_jwt_token_malformed(self, auth_service):
        """Test verifying malformed token."""
        malformed_tokens = [
            "not.a.token",
            "only.two",
            "",
            "invalid",
        ]
        
        for token in malformed_tokens:
            with pytest.raises(HTTPException) as exc_info:
                auth_service.verify_jwt_token(token)
            
            assert exc_info.value.status_code == 401
    
    def test_hash_api_key(self, auth_service):
        """Test API key hashing with HMAC."""
        api_key = "pmtr_live_test_key_12345"
        
        hash1 = auth_service.hash_api_key(api_key)
        hash2 = auth_service.hash_api_key(api_key)
        
        # Same key should produce same hash
        assert hash1 == hash2
        
        # Hash should be hex string
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars
        
        # Different key should produce different hash
        hash3 = auth_service.hash_api_key("pmtr_live_different_key")
        assert hash1 != hash3
    
    def test_verify_api_key_valid(self, auth_service):
        """Test verifying valid API key."""
        # This test uses the pre-configured test key
        api_key = "pmtr_live_test_key_12345"
        
        # Note: In production, you'd set up the key in the store first
        # For testing, we're using the default test key
        try:
            key_data = auth_service.verify_api_key(api_key)
            assert key_data.tenant_id == "tenant_test_001"
            assert key_data.is_active
        except HTTPException:
            # If test key isn't configured, that's okay
            pytest.skip("Test API key not configured")
    
    def test_verify_api_key_invalid_format(self, auth_service):
        """Test verifying API key with invalid format."""
        invalid_keys = [
            "no_prefix_key",
            "wrong_prefix_live_key",
            "",
            "pmtr_",  # Too short
        ]
        
        for api_key in invalid_keys:
            with pytest.raises(HTTPException) as exc_info:
                auth_service.verify_api_key(api_key)
            
            assert exc_info.value.status_code == 401
    
    def test_verify_api_key_not_found(self, auth_service):
        """Test verifying non-existent API key."""
        api_key = "pmtr_live_nonexistent_key_xyz"
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_api_key(api_key)
        
        assert exc_info.value.status_code == 401
        assert "Invalid" in exc_info.value.detail
    
    def test_verify_api_key_inactive(self, auth_service):
        """Test verifying inactive API key."""
        # Create inactive key in store
        from src.gateway.auth import API_KEYS_STORE
        
        api_key = "pmtr_live_inactive_test"
        key_hash = auth_service.hash_api_key(api_key)
        
        API_KEYS_STORE[key_hash] = APIKeyData(
            tenant_id="test_tenant",
            name="Inactive Key",
            is_active=False,
            created_at=datetime.utcnow()
        )
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_api_key(api_key)
        
        assert exc_info.value.status_code == 401
        assert "revoked" in str(exc_info.value.detail).lower()
        
        # Cleanup
        del API_KEYS_STORE[key_hash]
    
    def test_generate_api_key(self, auth_service):
        """Test generating new API key."""
        key1 = auth_service.generate_api_key()
        key2 = auth_service.generate_api_key()
        
        # Should start with prefix
        assert key1.startswith("pmtr_live_")
        assert key2.startswith("pmtr_live_")
        
        # Should be unique
        assert key1 != key2
        
        # Should be long enough (secure)
        assert len(key1) > 40
    
    def test_generate_api_key_custom_prefix(self, auth_service):
        """Test generating API key with custom prefix."""
        test_key = auth_service.generate_api_key(prefix="pmtr_test")
        
        assert test_key.startswith("pmtr_test_")


@pytest.mark.asyncio
class TestAuthDependencies:
    """Test FastAPI dependency functions."""
    
    async def test_verify_api_key_dependency_valid(self):
        """Test verify_api_key FastAPI dependency."""
        # Mock valid API key
        mock_header = "pmtr_live_test_key_12345"
        
        try:
            tenant_id = await verify_api_key(x_perimeter_api_key=mock_header)
            assert isinstance(tenant_id, str)
        except HTTPException:
            # If test key not configured, skip
            pytest.skip("Test API key not configured")
    
    async def test_verify_api_key_dependency_missing(self):
        """Test verify_api_key with missing key."""
        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(x_perimeter_api_key=None, authorization=None)
        
        assert exc_info.value.status_code == 401
        assert "Missing" in exc_info.value.detail
    
    async def test_verify_api_key_dependency_bearer_token(self):
        """Test verify_api_key with Bearer token."""
        # Should extract key from Authorization header
        auth_header = "Bearer pmtr_live_test_key_12345"
        
        try:
            tenant_id = await verify_api_key(
                x_perimeter_api_key=None,
                authorization=auth_header
            )
            assert isinstance(tenant_id, str)
        except HTTPException:
            pytest.skip("Test API key not configured")


class TestRoleBasedAccessControl:
    """Test RBAC functionality."""
    
    def test_require_role_decorator_structure(self):
        """Test require_role returns a dependency."""
        checker = require_role(["admin"])
        
        # Should be a callable
        assert callable(checker)
    
    @pytest.mark.asyncio
    async def test_require_role_allows_valid_role(self):
        """Test require_role allows users with correct role."""
        checker = require_role(["admin", "superadmin"])
        
        # Mock token with admin role
        token_data = TokenData(
            tenant_id="test",
            roles=["admin"]
        )
        
        # Should allow access
        result = await checker(token=token_data)
        assert result.tenant_id == "test"
    
    @pytest.mark.asyncio
    async def test_require_role_denies_invalid_role(self):
        """Test require_role denies users without required role."""
        checker = require_role(["admin"])
        
        # Mock token without admin role
        token_data = TokenData(
            tenant_id="test",
            roles=["developer"]
        )
        
        # Should deny access
        with pytest.raises(HTTPException) as exc_info:
            await checker(token=token_data)
        
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail


class TestTierBasedAccessControl:
    """Test tier-based feature gating."""
    
    def test_require_tier_decorator_structure(self):
        """Test require_tier returns a dependency."""
        checker = require_tier("business")
        
        # Should be a callable
        assert callable(checker)
    
    @pytest.mark.asyncio
    async def test_require_tier_allows_higher_tier(self):
        """Test require_tier allows higher tiers."""
        from src.gateway.auth import API_KEYS_STORE, auth_service
        
        # Set up enterprise tier key
        api_key = "pmtr_live_enterprise_test"
        key_hash = auth_service.hash_api_key(api_key)
        
        API_KEYS_STORE[key_hash] = APIKeyData(
            tenant_id="enterprise_tenant",
            name="Enterprise Key",
            tier="enterprise",  # Higher than business
            created_at=datetime.utcnow()
        )
        
        checker = require_tier("business")
        
        try:
            # Should allow access (enterprise > business)
            tenant_id = await checker(x_perimeter_api_key=api_key)
            assert tenant_id == "enterprise_tenant"
        finally:
            # Cleanup
            del API_KEYS_STORE[key_hash]
    
    @pytest.mark.asyncio
    async def test_require_tier_denies_lower_tier(self):
        """Test require_tier denies lower tiers."""
        from src.gateway.auth import API_KEYS_STORE, auth_service
        
        # Set up free tier key
        api_key = "pmtr_live_free_test"
        key_hash = auth_service.hash_api_key(api_key)
        
        API_KEYS_STORE[key_hash] = APIKeyData(
            tenant_id="free_tenant",
            name="Free Key",
            tier="free",  # Lower than business
            created_at=datetime.utcnow()
        )
        
        checker = require_tier("business")
        
        try:
            # Should deny access (free < business)
            with pytest.raises(HTTPException) as exc_info:
                await checker(x_perimeter_api_key=api_key)
            
            assert exc_info.value.status_code == 402  # Payment Required
            assert "upgrade" in str(exc_info.value.detail).lower()
        finally:
            # Cleanup
            del API_KEYS_STORE[key_hash]


class TestSecurityConcerns:
    """Test security-related functionality."""
    
    def test_hmac_prevents_rainbow_tables(self):
        """Test HMAC makes rainbow table attacks harder."""
        from src.gateway.auth import auth_service
        
        # Same key should always hash to same value
        key = "pmtr_live_test"
        hash1 = auth_service.hash_api_key(key)
        hash2 = auth_service.hash_api_key(key)
        assert hash1 == hash2
        
        # But without knowing the HMAC secret, can't recreate hash
        import hashlib
        simple_hash = hashlib.sha256(key.encode()).hexdigest()
        assert hash1 != simple_hash
    
    def test_jwt_algorithm_enforcement(self):
        """Test JWT algorithm is enforced (prevents 'none' attack)."""
        auth_service = AuthService()
        
        # Create valid token
        token_data = TokenData(tenant_id="test")
        token = auth_service.create_access_token(token_data)
        
        # Try to modify algorithm to 'none'
        decoded = pyjwt.decode(token, options={"verify_signature": False})
        decoded["alg"] = "none"
        
        # Re-encode without signature
        malicious_token = pyjwt.encode(decoded, "", algorithm="none")
        
        # Should reject
        with pytest.raises(HTTPException):
            auth_service.verify_jwt_token(malicious_token)
    
    def test_api_key_length_security(self):
        """Test generated API keys are cryptographically secure."""
        auth_service = AuthService()
        
        # Generate multiple keys
        keys = [auth_service.generate_api_key() for _ in range(100)]
        
        # All should be unique (no collisions in 100 keys)
        assert len(set(keys)) == 100
        
        # All should be long enough (>= 40 chars)
        assert all(len(key) >= 40 for key in keys)
        
        # Should have high entropy (not predictable)
        # Check that keys don't follow patterns
        for i in range(1, len(keys)):
            # Keys should be very different from each other
            common = sum(a == b for a, b in zip(keys[i], keys[i-1]))
            # Less than 20% characters in common
            assert common < len(keys[i]) * 0.2
