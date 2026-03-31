"""app/models/ad_slot.py"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base

class AdSlot(Base):
    __tablename__ = "ad_slots"
    __table_args__ = {"extend_existing": True}
    id          = Column(Integer, primary_key=True)
    slot_key    = Column(String(64), unique=True, nullable=False)  # "ticker_1"|"sidebar_top"
    slot_name   = Column(String(128), nullable=True)
    ad_type     = Column(String(32), default="banner")             # banner|native|text
    content     = Column(Text, nullable=True)
    link_url    = Column(String(512), nullable=True)
    image_url   = Column(String(512), nullable=True)
    advertiser  = Column(String(128), nullable=True)
    is_active   = Column(Boolean, default=False)
    start_at    = Column(DateTime(timezone=True), nullable=True)
    end_at      = Column(DateTime(timezone=True), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
