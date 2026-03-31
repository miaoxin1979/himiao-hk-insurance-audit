"""
app/models/subscriber.py

修复记录：
  - BUG-002: 原文件将 Subscriber、Broker、AdSlot 三个 class 混写在同一文件
    部分 class 缺少 `from app.db.base import Base` 导入
    base.py 执行 `from app.models import subscriber` 时触发 NameError
    导致应用启动失败，所有接口 500
  - 修复：subscriber.py 只保留 Subscriber model，干净独立
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class Subscriber(Base):
    """邮件订阅者"""
    __tablename__ = "subscribers"

    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String(128), unique=True, nullable=False, index=True)
    source     = Column(String(64), default="website")   # website | referral | campaign
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
