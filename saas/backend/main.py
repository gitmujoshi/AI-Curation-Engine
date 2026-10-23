"""
Perimeter SaaS Platform Backend

FastAPI application for managing users, API keys, billing, and analytics.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest
from fastapi.responses import Response

from src.cache.redis_client import RedisClient
from backend.routes import auth, keys, stats, billing, usage
from backend.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    logger.info("🚀 Perimeter SaaS Platform starting...")
    
    # Initialize database
    await init_db()
    
    # Initialize Redis
    redis_client = RedisClient("redis://localhost:6379/1")
    await redis_client.connect()
    app.state.redis = redis_client
    
    logger.info("✅ SaaS Platform initialized")
    
    yield
    
    # Cleanup
    await redis_client.close()
    logger.info("🛑 SaaS Platform shut down")


app = FastAPI(
    title="Perimeter SaaS API",
    description="Backend API for Perimeter SaaS Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://perimeter.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(keys.router, prefix="/api/keys", tags=["API Keys"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(usage.router, prefix="/api/usage", tags=["Usage"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Perimeter SaaS API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics."""
    return Response(content=generate_latest(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
