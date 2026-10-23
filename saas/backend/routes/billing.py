"""Billing and subscription routes"""

import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe

from backend.models.database import User, Subscription
from backend.database import get_db

router = APIRouter()

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


class BillingInfo(BaseModel):
    tier: str
    status: str
    currentPeriodEnd: str = None
    cancelAtPeriodEnd: bool = False


class CreateCheckoutSession(BaseModel):
    userId: str
    priceId: str


@router.get("/{user_id}", response_model=BillingInfo)
async def get_billing_info(user_id: str, db: Session = Depends(get_db)):
    """Get billing information for a user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    subscription = db.query(Subscription)\
        .filter(Subscription.user_id == user_id)\
        .filter(Subscription.status == "active")\
        .first()
    
    if subscription:
        return BillingInfo(
            tier=subscription.tier,
            status=subscription.status,
            currentPeriodEnd=subscription.current_period_end.isoformat(),
            cancelAtPeriodEnd=subscription.cancel_at_period_end
        )
    
    return BillingInfo(
        tier="free",
        status="active"
    )


@router.post("/create-session")
async def create_checkout_session(data: CreateCheckoutSession, db: Session = Depends(get_db)):
    """Create Stripe checkout session"""
    
    user = db.query(User).filter(User.id == data.userId).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Create or get Stripe customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": user.id}
            )
            user.stripe_customer_id = customer.id
            db.commit()
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": data.priceId,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard/billing?success=true",
            cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard/billing?canceled=true",
        )
        
        return {"sessionId": session.id, "url": session.url}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel-subscription")
async def cancel_subscription(user_id: str, db: Session = Depends(get_db)):
    """Cancel user subscription"""
    
    subscription = db.query(Subscription)\
        .filter(Subscription.user_id == user_id)\
        .filter(Subscription.status == "active")\
        .first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    try:
        # Cancel at period end
        stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            cancel_at_period_end=True
        )
        
        subscription.cancel_at_period_end = True
        db.commit()
        
        return {"message": "Subscription will be canceled at period end"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
