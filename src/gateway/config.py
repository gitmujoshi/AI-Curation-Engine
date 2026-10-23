"""
Configuration Management for Perimeter Gateway

Loads settings from environment variables with validation.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    # Application
    APP_NAME: str = "Perimeter Gateway"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # Security
    SECRET_KEY: str = "change-me-in-production"
    ALLOWED_ORIGINS: List[str] = ["*"]
    API_KEY_HEADER: str = "X-Perimeter-API-Key"
    
    # JWT Authentication
    JWT_SECRET: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    CACHE_TTL_SECONDS: int = 3600
    
    # Database (PostgreSQL)
    DATABASE_URL: str = "postgresql+asyncpg://perimeter:perimeter@localhost:5432/perimeter"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    
    # BAML Configuration
    BAML_SCHEMA_PATH: str = "config/baml_src"
    BAML_VALIDATE_INPUTS: bool = True
    BAML_VALIDATE_OUTPUTS: bool = True
    
    # Headroom Compression
    COMPRESSION_ENABLED: bool = True
    MIN_COMPRESSION_SIZE: int = 1024  # bytes
    TARGET_COMPRESSION_RATIO: float = 0.15  # 85% reduction
    
    # Content Router
    CODE_COMPRESSION_ENABLED: bool = True
    JSON_COMPRESSION_ENABLED: bool = True
    PROSE_COMPRESSION_ENABLED: bool = True
    
    # PII Detection
    PII_DETECTION_ENABLED: bool = True
    PII_ANONYMIZE: bool = True
    PII_DETECTION_THRESHOLD: float = 0.85
    
    # Guardrails
    PROMPT_INJECTION_DETECTION: bool = True
    JAILBREAK_DETECTION: bool = True
    MAX_PROMPT_LENGTH: int = 100000
    
    # LLM Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    ANTHROPIC_BASE_URL: str = "https://api.anthropic.com/v1"
    
    # Billing
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    BILLING_SYNC_INTERVAL_SECONDS: int = 3600
    PRICE_PER_1K_TOKENS: float = 0.001
    
    # Performance
    MAX_PROXY_LATENCY_MS: int = 5
    CACHE_HYDRATION_TIMEOUT_MS: int = 3
    REQUEST_TIMEOUT_SECONDS: int = 300
    
    # GCP Configuration
    GCP_PROJECT_ID: str = ""
    GCP_REGION: str = "us-central1"
    GCP_MEMORYSTORE_HOST: str = ""
    GCP_STORAGE_BUCKET: str = ""
    
    # Monitoring
    ENABLE_METRICS: bool = True
    ENABLE_TRACING: bool = True
    METRICS_PORT: int = 9090


settings = Settings()
