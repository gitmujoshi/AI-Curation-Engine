"""Statistics routes"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.database import Request, UsageSummary
from backend.database import get_db

router = APIRouter()


class StatsResponse(BaseModel):
    totalRequests: int
    tokensSaved: int
    avgCompression: str
    monthlyCost: float
    savedCost: float


@router.get("/{user_id}", response_model=StatsResponse)
async def get_stats(user_id: str, db: Session = Depends(get_db)):
    """Get user statistics"""
    
    # Get current month data
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    
    # Total requests
    total_requests = db.query(func.count(Request.id))\
        .filter(Request.user_id == user_id)\
        .filter(Request.timestamp >= month_start)\
        .scalar() or 0
    
    # Tokens saved
    tokens_saved = db.query(func.sum(Request.tokens_saved))\
        .filter(Request.user_id == user_id)\
        .filter(Request.timestamp >= month_start)\
        .scalar() or 0
    
    # Average compression
    avg_compression = db.query(func.avg(Request.compression_ratio))\
        .filter(Request.user_id == user_id)\
        .filter(Request.timestamp >= month_start)\
        .scalar() or 0.0
    
    # Monthly cost
    monthly_cost = db.query(func.sum(Request.cost))\
        .filter(Request.user_id == user_id)\
        .filter(Request.timestamp >= month_start)\
        .scalar() or 0.0
    
    # Calculate saved cost (assuming $0.001 per 1K tokens)
    saved_cost = (tokens_saved / 1000) * 0.001
    
    return StatsResponse(
        totalRequests=total_requests,
        tokensSaved=int(tokens_saved),
        avgCompression=f"{avg_compression:.1f}%",
        monthlyCost=monthly_cost,
        savedCost=saved_cost
    )
