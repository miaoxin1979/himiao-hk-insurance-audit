"""app/models/user.py"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(64), unique=True, nullable=False, index=True)
    email      = Column(String(128), unique=True, nullable=True)
    hashed_pw  = Column(String(256), nullable=False)
    role       = Column(String(32), default="admin")   # admin | editor | viewer（后台）
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
