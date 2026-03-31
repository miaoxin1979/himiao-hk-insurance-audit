"""
app/api/v1/endpoints/products_savings.py
储蓄分红险 CRUD — 读写真实 SQLite DB
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_editor
from app.models.product import Product, ProductType
from app.models.user import User
from app.models.products_typed import SavingsProductCreate, SavingsProductUpdate, SavingsProductOut

router = APIRouter(prefix="/products/savings", tags=["Products · Savings"])


def _to_out(p: Product) -> SavingsProductOut:
    specs = p.specifications or {}
    return SavingsProductOut(
        id=p.id,
        product_code=p.slug,
        insurer=p.company,
        insurer_full=p.company_full,
        product_name_cn=p.title_zh,
        product_name_en=p.title_en,
        currency=p.currency or "USD",
        premium_years=p.premium_years,
        premium_annual=p.premium_annual,
        is_published=p.is_published,
        data_source_url=p.source_pdf_url,
        audit_note=specs.get("audit_note"),
        irr_20y=p.irr_20y,
        irr_10y=specs.get("irr_10y"),
        breakeven_year=p.breakeven_year,
        dividend_fulfillment_5y=p.dividend_fulfillment_5y,
        non_guaranteed_ratio=specs.get("non_guaranteed_ratio"),
        max_early_exit_loss_pct=p.max_early_exit_loss_pct,
        policy_loan_ltv=p.loan_ltv,
        guaranteed_cash_value_10y=specs.get("guaranteed_cash_value_10y"),
        total_cash_value_20y=specs.get("total_cash_value_20y"),
    )


def _apply(p: Product, body: SavingsProductCreate) -> None:
    p.slug            = body.product_code
    p.company         = body.insurer
    p.company_full    = body.insurer_full
    p.title_zh        = body.product_name_cn
    p.title_en        = body.product_name_en
    p.currency        = body.currency
    p.premium_years   = body.premium_years
    p.premium_annual  = body.premium_annual
    p.is_published    = body.is_published
    p.source_pdf_url  = body.data_source_url
    p.irr_20y                 = body.irr_20y
    p.breakeven_year          = body.breakeven_year
    p.dividend_fulfillment_5y = body.dividend_fulfillment_5y
    p.max_early_exit_loss_pct = body.max_early_exit_loss_pct
    p.loan_ltv                = body.policy_loan_ltv
    p.specifications = {
        "irr_10y":                  body.irr_10y,
        "non_guaranteed_ratio":     body.non_guaranteed_ratio,
        "guaranteed_cash_value_10y":body.guaranteed_cash_value_10y,
        "total_cash_value_20y":     body.total_cash_value_20y,
        "audit_note":               body.audit_note,
    }


@router.get("", response_model=List[SavingsProductOut], summary="储蓄险列表")
def list_savings(
    is_published: Optional[bool] = Query(None),
    insurer:      Optional[str]  = Query(None),
    limit:        int            = Query(50, ge=1, le=200),
    offset:       int            = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.product_type == ProductType.SAVINGS)
    if is_published is not None:
        q = q.filter(Product.is_published == is_published)
    if insurer:
        q = q.filter(Product.company.ilike(insurer))
    return [_to_out(p) for p in q.offset(offset).limit(limit).all()]


@router.get("/{product_code}", response_model=SavingsProductOut, summary="储蓄险详情")
def get_savings(product_code: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(
        Product.product_type == ProductType.SAVINGS,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    return _to_out(p)


@router.post("", response_model=SavingsProductOut, status_code=201, summary="新建储蓄险")
def create_savings(
    body: SavingsProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    if db.query(Product).filter(Product.slug == body.product_code).first():
        raise HTTPException(status_code=409, detail=f"product_code '{body.product_code}' 已存在")
    p = Product(product_type=ProductType.SAVINGS)
    _apply(p, body)
    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.put("/{product_code}", response_model=SavingsProductOut, summary="全量更新储蓄险")
def replace_savings(
    product_code: str,
    body: SavingsProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(
        Product.product_type == ProductType.SAVINGS,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    _apply(p, body)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.patch("/{product_code}", response_model=SavingsProductOut, summary="局部更新储蓄险")
def update_savings(
    product_code: str,
    body: SavingsProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(
        Product.product_type == ProductType.SAVINGS,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    patch = body.model_dump(exclude_unset=True)
    specs = dict(p.specifications or {})
    field_map = {
        "insurer": "company", "insurer_full": "company_full",
        "product_name_cn": "title_zh", "product_name_en": "title_en",
        "premium_years": "premium_years", "premium_annual": "premium_annual",
        "is_published": "is_published", "data_source_url": "source_pdf_url",
        "irr_20y": "irr_20y", "breakeven_year": "breakeven_year",
        "dividend_fulfillment_5y": "dividend_fulfillment_5y",
        "max_early_exit_loss_pct": "max_early_exit_loss_pct",
        "policy_loan_ltv": "loan_ltv",
    }
    json_fields = {"irr_10y", "non_guaranteed_ratio", "guaranteed_cash_value_10y",
                   "total_cash_value_20y", "audit_note"}
    for k, v in patch.items():
        if k in field_map:
            setattr(p, field_map[k], v)
        elif k in json_fields:
            specs[k] = v
    p.specifications = specs
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.delete("/{product_code}", status_code=204, summary="删除储蓄险")
def delete_savings(
    product_code: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(
        Product.product_type == ProductType.SAVINGS,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    db.delete(p)
    db.commit()
