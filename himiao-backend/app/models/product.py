"""
app/models/product.py
三大险种：储蓄分红险 / 终身寿险 / 重疾险
"""
import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, JSON
from sqlalchemy import Enum as SAEnum
from sqlalchemy.sql import func
from app.db.base import Base


class ProductType(str, enum.Enum):
    SAVINGS          = "savings"           # 储蓄分红险
    WHOLE_LIFE       = "whole_life"        # 终身寿险
    CRITICAL_ILLNESS = "critical_illness"  # 重疾险


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"extend_existing": True}

    id   = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, nullable=False, index=True)

    # ── 险种分类（核心新增，驱动全站过滤）──────────────────
    product_type = Column(
        SAEnum(ProductType, name="product_type_enum",
               values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ProductType.SAVINGS,
        index=True,   # 高频过滤字段
    )

    # ── 基础 meta ───────────────────────────────────────────
    title_zh     = Column(String(128), nullable=False)
    title_tw     = Column(String(128), nullable=True)
    title_en     = Column(String(128), nullable=True)
    company      = Column(String(64),  nullable=False)
    company_full = Column(String(128), nullable=True)
    logo_url     = Column(String(512), nullable=True)
    currency     = Column(String(8),   default="USD")
    rating       = Column(String(16),  nullable=True)
    version      = Column(String(32),  nullable=True)
    highlight    = Column(Boolean,     default=False)

    # ── 通用精算核心字段（扁平化，支持排序/范围查询）────────
    premium_years           = Column(Integer, nullable=True)
    premium_annual          = Column(Float,   nullable=True)
    breakeven_year          = Column(Integer, nullable=True)
    irr_20y                 = Column(Float,   nullable=True)
    loan_ltv                = Column(Float,   nullable=True)
    dividend_fulfillment_5y = Column(Float,   nullable=True)
    max_early_exit_loss_pct = Column(Float,   nullable=True)

    # ── 医疗险快速筛选字段（扁平化，避免 JSON 查询）────────
    annual_limit_hkd  = Column(Float,   nullable=True)   # 年度保障上限
    deductible_min    = Column(Float,   nullable=True)   # 最低免赔额

    # ── 重疾险快速筛选字段 ────────────────────────────────
    covered_conditions_count = Column(Integer, nullable=True)  # 保障病种数
    multi_pay                = Column(Boolean, nullable=True)  # 多重赔付

    # ── 险种特有数据（JSON 灵活存储）────────────────────────
    # 结构见文件头部注释；SQLite 存 TEXT，PostgreSQL 存 JSONB，零代码切换
    specifications = Column(JSON, nullable=True)

    # ── 遗留 JSON 字段（向后兼容保留）──────────────────────
    scenarios_json = Column(JSON, nullable=True)
    timeline_json  = Column(JSON, nullable=True)
    scores_json    = Column(JSON, nullable=True)

    # ── 精算辣评（三语）─────────────────────────────────────
    content_zh    = Column(Text, nullable=True)   # 简体
    content_tw    = Column(Text, nullable=True)   # 繁体
    content_en    = Column(Text, nullable=True)   # English

    # ── 合规字段 ─────────────────────────────────────────────
    # 版权合规：只存保司官网原始 URL，前端重定向，不存 PDF 文件
    source_pdf_url = Column(String(512), nullable=True)
    # 数据信任：AI 提取的数据前端需显示合规 Tooltip
    ai_extracted   = Column(Boolean, default=False)
    # 人工审核锁：爬虫/OCR 写入默认 False，管理员审核后手动改 True
    launch_year    = Column(Integer, nullable=True)
    is_published   = Column(Boolean, default=False)

    # ── 时间戳 ──────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
