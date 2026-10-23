"""Database models for SaaS platform"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User account model"""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)  # Clerk user ID
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    organization = Column(String)
    tier = Column(String, default="free")  # free, pro, enterprise
    stripe_customer_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    requests = relationship("Request", back_populates="user", cascade="all, delete-orphan")


class ApiKey(Base):
    """API key model"""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    key = Column(String, unique=True, nullable=False)
    name = Column(String)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    
    user = relationship("User", back_populates="api_keys")


class Request(Base):
    """Request log model"""
    __tablename__ = "requests"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    api_key_id = Column(String, ForeignKey("api_keys.id"))
    model = Column(String, nullable=False)
    status = Column(String, nullable=False)  # success, error
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    tokens_saved = Column(Integer, default=0)
    compression_ratio = Column(Float, default=0.0)
    latency_ms = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="requests")


class UsageSummary(Base):
    """Daily usage summary"""
    __tablename__ = "usage_summaries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    total_requests = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    tokens_saved = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    avg_compression = Column(Float, default=0.0)
    avg_latency = Column(Float, default=0.0)


class Subscription(Base):
    """Subscription model"""
    __tablename__ = "subscriptions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True)
    tier = Column(String, nullable=False)  # free, pro, enterprise
    status = Column(String, nullable=False)  # active, canceled, past_due
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
