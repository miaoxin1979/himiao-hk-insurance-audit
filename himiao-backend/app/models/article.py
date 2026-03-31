"""app/models/article.py"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = {"extend_existing": True}

    id          = Column(Integer, primary_key=True, index=True)
    slug        = Column(String(128), unique=True, nullable=False, index=True)
    title_zh    = Column(String(256), nullable=False)
    title_tw    = Column(String(256), nullable=True)
    title_en    = Column(String(256), nullable=True)
    excerpt     = Column(Text, nullable=True)
    content_zh  = Column(Text, nullable=True)         # Markdown 正文
    content_tw  = Column(Text, nullable=True)
    content_en  = Column(Text, nullable=True)
    source_url  = Column(String(512), nullable=True)   # 原文链接（爬虫来源）
    cover_url   = Column(String(512), nullable=True)
    category    = Column(String(32), nullable=True)   # market|alert|policy|audit|guide
    channel     = Column(String(16), nullable=True)   # news | academy（NULL 视为 news）
    content_format = Column(String(16), nullable=True)  # markdown | html（NULL 视为 markdown）
    tags        = Column(JSON, nullable=True)          # ["储蓄险","AIA"]
    author      = Column(String(64), default="HiMiao 精算团队")
    read_min    = Column(Integer, default=5)
    is_hot      = Column(Boolean, default=False)
    is_published = Column(Boolean, default=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())
