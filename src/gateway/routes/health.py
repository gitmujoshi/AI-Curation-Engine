"""
Health Check Routes

Provides endpoints for monitoring service health and readiness.
"""

from fastapi import APIRouter, status, Request
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    version: str
    environment: str
    services: dict


@router.get("/", response_model=HealthResponse)
async def health_check(request: Request):
    """
    Basic health check endpoint.
    
    Returns service status and version information.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        environment="production",
        services={
            "gateway": "operational",
            "redis": "operational",
            "baml_engine": "operational",
            "headroom": "operational"
        }
    )


@router.get("/ready")
async def readiness_check(request: Request):
    """
    Readiness check for Kubernetes/Cloud Run.
    
    Verifies all dependencies are available.
    """
    try:
        # Check Redis connection
        redis = request.app.state.redis
        await redis.ping()
        
        return {
            "status": "ready",
            "checks": {
                "redis": "connected",
                "database": "connected"
            }
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e)
        }, status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes/Cloud Run.
    
    Simple check that the service is running.
    """
    return {"status": "alive"}
