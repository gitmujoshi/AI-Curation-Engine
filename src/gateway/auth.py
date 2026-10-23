"""
Authentication & Authorization

JWT/OAuth2-based authentication with proper token validation,
role-based access control (RBAC), and API key management.
"""

import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List

import jwt
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from src.gateway.config import settings

logger = logging.getLogger(__name__)

# Security schemes
security = HTTPBearer()


class TokenData(BaseModel):
    """JWT token payload data."""
    tenant_id: str
    user_id: Optional[str] = None
    roles: List[str] = []
    tier: str = "free"
    rate_limit: int = 100  # requests per minute


class APIKeyData(BaseModel):
    """API key metadata."""
    tenant_id: str
    name: str
    tier: str = "free"
    rate_limit: int = 100
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True


# In production, these would be in Redis/PostgreSQL
# This is just for demonstration
API_KEYS_STORE: Dict[str, APIKeyData] = {
    # Example: SHA-256 hash of "pmtr_live_test_key_12345"
    "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8": APIKeyData(
        tenant_id="tenant_test_001",
        name="Test Organization",
        tier="enterprise",
        rate_limit=1000,
        created_at=datetime.utcnow(),
        is_active=True
    )
}


class AuthService:
    """
    Centralized authentication service.
    
    Supports:
    - JWT token validation (OAuth2)
    - API key validation (with HMAC)
    - Rate limiting metadata
    - Role-based access control
    """
    
    def __init__(self):
        self.jwt_secret = settings.JWT_SECRET if hasattr(settings, 'JWT_SECRET') else "your-secret-key-change-in-production"
        self.jwt_algorithm = "HS256"
        self.jwt_expiration = timedelta(hours=24)
    
    def create_access_token(self, data: TokenData) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Token payload data
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.model_dump()
        expire = datetime.utcnow() + self.jwt_expiration
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.jwt_secret,
            algorithm=self.jwt_algorithm
        )
        
        return encoded_jwt
    
    def verify_jwt_token(self, token: str) -> TokenData:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token data
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
            
            token_data = TokenData(
                tenant_id=payload.get("tenant_id"),
                user_id=payload.get("user_id"),
                roles=payload.get("roles", []),
                tier=payload.get("tier", "free"),
                rate_limit=payload.get("rate_limit", 100)
            )
            
            return token_data
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def hash_api_key(self, api_key: str) -> str:
        """
        Create SHA-256 hash of API key for secure storage.
        
        Uses HMAC with secret for additional security.
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Hexadecimal hash string
        """
        # Use HMAC for additional security
        return hmac.new(
            self.jwt_secret.encode(),
            api_key.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_api_key(self, api_key: str) -> APIKeyData:
        """
        Verify API key and return metadata.
        
        Args:
            api_key: API key from request
            
        Returns:
            API key metadata
            
        Raises:
            HTTPException: If API key is invalid
        """
        # Validate format
        if not api_key.startswith("pmtr_"):
            logger.warning(f"Invalid API key format: {api_key[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format"
            )
        
        # Hash the key
        key_hash = self.hash_api_key(api_key)
        
        # Look up in store (in production: Redis cache → Database)
        key_data = API_KEYS_STORE.get(key_hash)
        
        if not key_data:
            logger.warning(f"API key not found: {api_key[:15]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        if not key_data.is_active:
            logger.warning(f"Inactive API key used: {key_data.tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been revoked"
            )
        
        # Update last used timestamp (in production: async update)
        key_data.last_used = datetime.utcnow()
        
        logger.info(f"API key authenticated for tenant: {key_data.tenant_id}")
        return key_data
    
    def generate_api_key(self, prefix: str = "pmtr_live") -> str:
        """
        Generate a new cryptographically secure API key.
        
        Args:
            prefix: Key prefix (e.g., "pmtr_live", "pmtr_test")
            
        Returns:
            New API key
        """
        # Generate 32 bytes of random data
        random_bytes = secrets.token_bytes(32)
        
        # Encode as base62 (alphanumeric)
        key_suffix = secrets.token_urlsafe(32)
        
        return f"{prefix}_{key_suffix}"


# Global auth service instance
auth_service = AuthService()


# Dependency for JWT authentication
async def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    FastAPI dependency for JWT authentication.
    
    Usage:
        @app.get("/protected")
        async def protected_route(token: TokenData = Depends(verify_jwt)):
            return {"tenant_id": token.tenant_id}
    """
    return auth_service.verify_jwt_token(credentials.credentials)


# Dependency for API key authentication
async def verify_api_key(
    x_perimeter_api_key: Optional[str] = Header(None, alias="X-Perimeter-API-Key"),
    authorization: Optional[str] = Header(None)
) -> str:
async def verify_api_key(
    x_perimeter_api_key: Optional[str] = Header(None, alias="X-Perimeter-API-Key"),
    authorization: Optional[str] = Header(None)
) -> str:
    """
    FastAPI dependency for API key authentication.
    
    Supports two auth methods:
    1. X-Perimeter-API-Key header (preferred)
    2. Authorization: Bearer <api_key> header (alternative)
    
    Args:
        x_perimeter_api_key: API key from custom header
        authorization: API key from Authorization header
        
    Returns:
        tenant_id: Unique identifier for the tenant
        
    Raises:
        HTTPException: If API key is invalid or missing
        
    Usage:
        @app.post("/v1/chat/completions")
        async def chat(tenant_id: str = Depends(verify_api_key)):
            return {"tenant_id": tenant_id}
    """
    api_key = None
    
    # Try custom header first
    if x_perimeter_api_key:
        api_key = x_perimeter_api_key
    # Try Bearer token
    elif authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:]  # Remove "Bearer " prefix
    
    if not api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide via X-Perimeter-API-Key header or Authorization: Bearer <key>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the key
    key_data = auth_service.verify_api_key(api_key)
    
    return key_data.tenant_id


# Role-based access control decorator
def require_role(required_roles: List[str]):
    """
    Decorator to enforce role-based access control.
    
    Usage:
        @app.get("/admin/users")
        @require_role(["admin", "superadmin"])
        async def list_users(token: TokenData = Depends(verify_jwt)):
            return {"users": [...]}
    """
    async def role_checker(token: TokenData = Depends(verify_jwt)) -> TokenData:
        if not any(role in token.roles for role in required_roles):
            logger.warning(
                f"Access denied for tenant {token.tenant_id}: "
                f"requires {required_roles}, has {token.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        return token
    
    return role_checker


# Tier-based access control
def require_tier(minimum_tier: str):
    """
    Decorator to enforce tier-based access control.
    
    Tiers (in order): free < startup < growth < business < enterprise
    
    Usage:
        @app.post("/v1/advanced-features")
        async def advanced_feature(tenant_id: str = Depends(require_tier("business"))):
            return {"feature": "enabled"}
    """
    tier_hierarchy = ["free", "startup", "growth", "business", "enterprise"]
    min_tier_level = tier_hierarchy.index(minimum_tier)
    
    async def tier_checker(
        x_perimeter_api_key: Optional[str] = Header(None, alias="X-Perimeter-API-Key"),
        authorization: Optional[str] = Header(None)
    ) -> str:
        # Get API key
        api_key = x_perimeter_api_key
        if not api_key and authorization and authorization.startswith("Bearer "):
            api_key = authorization[7:]
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API key"
            )
        
        # Verify and check tier
        key_data = auth_service.verify_api_key(api_key)
        current_tier_level = tier_hierarchy.index(key_data.tier)
        
        if current_tier_level < min_tier_level:
            logger.warning(
                f"Tier restriction: tenant {key_data.tenant_id} "
                f"has {key_data.tier}, needs {minimum_tier}"
            )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"This feature requires {minimum_tier} tier or higher. "
                       f"Current tier: {key_data.tier}. Please upgrade your plan."
            )
        
        return key_data.tenant_id
    
    return tier_checker


# Utility functions
def hash_api_key(api_key: str) -> str:
    """
    Create SHA-256 hash of API key for secure storage.
    
    Args:
        api_key: Plain text API key
        
    Returns:
        Hexadecimal hash string
        
    Deprecated: Use auth_service.hash_api_key() instead
    """
    return auth_service.hash_api_key(api_key)
