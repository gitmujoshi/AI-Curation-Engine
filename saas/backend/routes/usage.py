"""Usage analytics routes"""

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.database import Request, UsageSummary
from backend.database import get_db

router = APIRouter()


class UsageChartPoint(BaseModel):
    date: str
    requests: int
    tokensSaved: int


class RecentRequestResponse(BaseModel):
    id: str
    model: str
    status: str
    tokens: int
    latency: int
    compressionRatio: float
    timestamp: datetime


@router.get("/chart/{user_id}", response_model=List[UsageChartPoint])
async def get_usage_chart(user_id: str, db: Session = Depends(get_db)):
    """Get usage chart data for last 30 days"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    
    # Get daily summaries
    summaries = db.query(
        func.date(Request.timestamp).label('date'),
        func.count(Request.id).label('requests'),
        func.sum(Request.tokens_saved).label('tokens_saved')
    )\
    .filter(Request.user_id == user_id)\
    .filter(Request.timestamp >= start_date)\
    .group_by(func.date(Request.timestamp))\
    .all()
    
    # Format response
    chart_data = []
    for summary in summaries:
        chart_data.append(UsageChartPoint(
            date=summary.date.strftime('%Y-%m-%d'),
            requests=summary.requests,
            tokensSaved=int(summary.tokens_saved or 0)
        ))
    
    return chart_data


@router.get("/recent/{user_id}", response_model=List[RecentRequestResponse])
async def get_recent_requests(user_id: str, db: Session = Depends(get_db)):
    """Get recent requests for a user"""
    
    requests = db.query(Request)\
        .filter(Request.user_id == user_id)\
        .order_by(Request.timestamp.desc())\
        .limit(10)\
        .all()
    
    return [
        RecentRequestResponse(
            id=req.id,
            model=req.model,
            status=req.status,
            tokens=req.tokens_input + req.tokens_output,
            latency=req.latency_ms,
            compressionRatio=req.compression_ratio,
            timestamp=req.timestamp
        )
        for req in requests
    ]
