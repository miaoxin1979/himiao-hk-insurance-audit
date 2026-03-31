"""app/models/broker.py"""
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Float
from sqlalchemy.sql import func
from app.db.base import Base

class Broker(Base):
    __tablename__ = "brokers"
    __table_args__ = {"extend_existing": True}
    id           = Column(Integer, primary_key=True)
    name         = Column(String(64), nullable=False)
    license_no   = Column(String(64), nullable=True)
    company      = Column(String(128), nullable=True)
    phone        = Column(String(32), nullable=True)
    email        = Column(String(128), nullable=True)
    wechat       = Column(String(64), nullable=True)
    intro        = Column(Text, nullable=True)
    avatar_url   = Column(String(512), nullable=True)
    rating       = Column(Float, default=5.0)
    specialties  = Column(String(256), nullable=True)
    is_verified  = Column(Boolean, default=False)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
