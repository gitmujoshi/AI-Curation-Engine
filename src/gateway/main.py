"""
Perimeter AI Security Gateway - Main Application Entry Point

This module initializes the FastAPI application and orchestrates all core components:
- BAML Type Guardrail Engine
- Headroom Content Compression & Caching
- PII Detection & Safety Guardrails
- Egress Control & Payload Assembly
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest

from src.gateway.config import settings
from src.gateway.routes import health, proxy
from src.cache.redis_client import RedisClient
from src.billing.usage_tracker import UsageTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "perimeter_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"]
)
REQUEST_DURATION = Histogram(
    "perimeter_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"]
)
COMPRESSION_RATIO = Histogram(
    "perimeter_compression_ratio",
    "Payload compression ratio",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager - handles startup and shutdown."""
    logger.info("🚀 Perimeter Gateway starting up...")
    
    # Initialize Redis connection pool
    redis_client = RedisClient(settings.REDIS_URL)
    await redis_client.connect()
    app.state.redis = redis_client
    
    # Initialize usage tracker
    usage_tracker = UsageTracker(redis_client)
    app.state.usage_tracker = usage_tracker
    
    logger.info("✅ All services initialized successfully")
    logger.info(f"🔒 Running in {settings.ENVIRONMENT} environment")
    logger.info(f"🌍 Listening on {settings.HOST}:{settings.PORT}")
    
    yield
    
    # Cleanup
    logger.info("🛑 Perimeter Gateway shutting down...")
    await redis_client.close()
    logger.info("✅ Cleanup completed")


app = FastAPI(
    title="Perimeter AI Security Gateway",
    description="Enterprise-Grade AI Security Gateway for Safe LLM Deployments",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time and metrics to each request."""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(proxy.router, prefix="/v1", tags=["Proxy"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Perimeter AI Security Gateway",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.ENVIRONMENT != "production" else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.gateway.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
