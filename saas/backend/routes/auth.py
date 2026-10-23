"""Authentication routes"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models.database import User
from backend.database import get_db

router = APIRouter()


class UserCreate(BaseModel):
    id: str  # Clerk user ID
    email: str
    name: str = None
    organization: str = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str = None
    organization: str = None
    tier: str


@router.post("/register", response_model=UserResponse)
async def register_user(data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    
    # Check if user exists
    existing = db.query(User).filter(User.id == data.id).first()
    if existing:
        return UserResponse(
            id=existing.id,
            email=existing.email,
            name=existing.name,
            organization=existing.organization,
            tier=existing.tier
        )
    
    # Create user
    user = User(
        id=data.id,
        email=data.email,
        name=data.name,
        organization=data.organization,
        tier="free"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        organization=user.organization,
        tier=user.tier
    )


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID"""
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        organization=user.organization,
        tier=user.tier
    )
