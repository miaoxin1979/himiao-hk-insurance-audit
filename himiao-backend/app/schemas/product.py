"""
app/schemas/product.py — 全险种重构版
"""
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from datetime import datetime
from app.models.product import ProductType


class ProductBase(BaseModel):
    slug:         str
    title_zh:     str
    title_tw:     Optional[str] = None
    title_en:     Optional[str] = None
    company:      str
    company_full: Optional[str] = None
    logo_url:     Optional[str] = None
    currency:     str = "USD"
    rating:       Optional[str] = None
    product_type: ProductType = ProductType.SAVINGS
    version:      Optional[str] = None
    highlight:    Optional[bool] = False

    # 通用精算字段
    premium_years:           Optional[int]   = None
    premium_annual:          Optional[float] = None
    breakeven_year:          Optional[int]   = None
    irr_20y:                 Optional[float] = None
    loan_ltv:                Optional[float] = None
    dividend_fulfillment_5y: Optional[float] = None
    max_early_exit_loss_pct: Optional[float] = None

    # 医疗险快速筛选
    annual_limit_hkd: Optional[float] = None
    deductible_min:   Optional[float] = None

    # 重疾险快速筛选
    covered_conditions_count: Optional[int]  = None
    multi_pay:                Optional[bool] = None

    # 险种特有数据（JSON）
    specifications: Optional[Dict[str, Any]] = None

    # 遗留字段（向后兼容）
    scenarios_json: Optional[Dict[str, Any]] = None
    timeline_json:  Optional[Dict[str, Any]] = None
    scores_json:    Optional[Dict[str, Any]] = None

    content_zh: Optional[str] = None
    content_tw: Optional[str] = None
    content_en: Optional[str] = None

    # 合规字段
    source_pdf_url: Optional[str]  = None   # 保司官网原始 URL，不存文件
    ai_extracted:   Optional[bool] = False
    is_published:   Optional[bool] = False   # 默认 False，人工审核锁


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    """PATCH 语义：所有字段可选"""
    title_zh:     Optional[str]            = None
    title_tw:     Optional[str]            = None
    title_en:     Optional[str]            = None
    company:      Optional[str]            = None
    product_type: Optional[ProductType]    = None
    highlight:    Optional[bool]           = None
    premium_years:           Optional[int]   = None
    premium_annual:          Optional[float] = None
    breakeven_year:          Optional[int]   = None
    irr_20y:                 Optional[float] = None
    loan_ltv:                Optional[float] = None
    dividend_fulfillment_5y: Optional[float] = None
    annual_limit_hkd:        Optional[float] = None
    deductible_min:          Optional[float] = None
    covered_conditions_count: Optional[int]  = None
    multi_pay:                Optional[bool] = None
    specifications:          Optional[Dict[str, Any]] = None
    scenarios_json:          Optional[Dict[str, Any]] = None
    timeline_json:           Optional[Dict[str, Any]] = None
    scores_json:             Optional[Dict[str, Any]] = None
    content_zh:   Optional[str]  = None
    content_tw:   Optional[str]  = None
    content_en:   Optional[str]  = None
    source_pdf_url: Optional[str] = None
    ai_extracted:   Optional[bool] = None
    launch_year:    Optional[int]  = None
    is_published:   Optional[bool] = None


class ProductOut(ProductBase):
    id:         int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class ProductPublic(BaseModel):
    """前端公开接口 — 保持与原 products.json 格式兼容"""
    id:          str
    product_type: str
    highlight:   bool = False
    ai_extracted: bool = False   # 前端据此决定是否显示合规 Tooltip
    source_pdf_url: Optional[str] = None  # 前端重定向用
    meta:        Dict[str, Any]
    actuarial:   Dict[str, Any]
    audit_data:  Dict[str, Any]
    scores:      Optional[Dict[str, Any]] = None
    specifications: Optional[Dict[str, Any]] = None
    review:      Optional[str] = None
