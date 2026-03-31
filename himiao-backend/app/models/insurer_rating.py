"""
app/models/insurer_rating.py
保司信用评级 — 须来自官方披露（标普/穆迪/惠誉），合规可追溯
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text
from sqlalchemy.sql import func
from app.db.base import Base


class InsurerRating(Base):
    """
    保司信用评级（按公司维度，非按产品）
    数据须来自官方披露，source_url 必填以合规可追溯
    """
    __tablename__ = "insurer_ratings"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    # 保司名（与 Product.company 匹配，如 AIA / 友邦 / Prudential / 保诚）
    company = Column(String(64), nullable=False, index=True)

    # 评级值，如 AA+ / AA- / A+（统一用标普体系展示时可注明 agency）
    rating = Column(String(16), nullable=False)

    # 评级机构：S&P / Moody's / Fitch
    agency = Column(String(32), nullable=False, default="S&P")

    # 官方披露链接（必填，合规可追溯）
    source_url = Column(Text, nullable=False)

    # 评级生效/披露日期
    as_of_date = Column(Date, nullable=True)

    # 备注（如：集团层面/香港子公司等）
    note = Column(String(256), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
