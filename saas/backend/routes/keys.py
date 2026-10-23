"""API Keys management routes"""

import secrets
import hashlib
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.database import ApiKey, User
from backend.database import get_db

router = APIRouter()


class ApiKeyCreate(BaseModel):
    userId: str
    name: str = "Default Key"


class ApiKeyResponse(BaseModel):
    id: str
    key: str
    name: str
    active: bool
    createdAt: datetime
    lastUsed: datetime = None


def generate_api_key() -> str:
    """Generate a secure API key"""
    random_part = secrets.token_urlsafe(32)
    return f"pmtr_live_{random_part}"


@router.get("/{user_id}", response_model=List[ApiKeyResponse])
async def get_api_keys(user_id: str, db: Session = Depends(get_db)):
    """Get all API keys for a user"""
    keys = db.query(ApiKey).filter(ApiKey.user_id == user_id).all()
    return [
        ApiKeyResponse(
            id=key.id,
            key=key.key,
            name=key.name or "API Key",
            active=key.active,
            createdAt=key.created_at,
            lastUsed=key.last_used
        )
        for key in keys
    ]


@router.post("", response_model=ApiKeyResponse)
async def create_api_key(data: ApiKeyCreate, db: Session = Depends(get_db)):
    """Create a new API key"""
    # Generate key
    key_value = generate_api_key()
    key_id = hashlib.sha256(key_value.encode()).hexdigest()[:16]
    
    # Create key
    api_key = ApiKey(
        id=key_id,
        user_id=data.userId,
        key=key_value,
        name=data.name,
        active=True
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    return ApiKeyResponse(
        id=api_key.id,
        key=api_key.key,
        name=api_key.name,
        active=api_key.active,
        createdAt=api_key.created_at,
        lastUsed=api_key.last_used
    )


@router.delete("/{key_id}")
async def delete_api_key(key_id: str, db: Session = Depends(get_db)):
    """Delete an API key"""
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(key)
    db.commit()
    
    return {"message": "API key deleted"}


@router.patch("/{key_id}/toggle")
async def toggle_api_key(key_id: str, db: Session = Depends(get_db)):
    """Toggle API key active status"""
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key.active = not key.active
    db.commit()
    
    return {"active": key.active}
