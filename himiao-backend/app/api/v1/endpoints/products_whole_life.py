"""
app/api/v1/endpoints/products_whole_life.py
终身寿险 CRUD — 读写真实 SQLite DB
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_editor
from app.models.product import Product, ProductType
from app.models.user import User
from app.models.products_typed import WholeLifeProductCreate, WholeLifeProductUpdate, WholeLifeProductOut

router = APIRouter(prefix="/products/whole_life", tags=["Products · Whole Life"])


def _to_out(p: Product) -> WholeLifeProductOut:
    specs = p.specifications or {}
    return WholeLifeProductOut(
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
        irr_30y=specs.get("irr_30y"),
        breakeven_year=p.breakeven_year,
        dividend_fulfillment_5y=p.dividend_fulfillment_5y,
        non_guaranteed_ratio=specs.get("non_guaranteed_ratio"),
        policy_loan_ltv=p.loan_ltv,
        death_benefit_guaranteed_pct=specs.get("death_benefit_guaranteed_pct"),
        death_benefit_total_20y_pct=specs.get("death_benefit_total_20y_pct"),
        cash_value_10y=specs.get("cash_value_10y"),
        cash_value_20y=specs.get("cash_value_20y"),
        max_early_exit_loss_pct=p.max_early_exit_loss_pct,
    )


def _apply(p: Product, body: WholeLifeProductCreate) -> None:
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
        "irr_30y":                       body.irr_30y,
        "non_guaranteed_ratio":          body.non_guaranteed_ratio,
        "death_benefit_guaranteed_pct":  body.death_benefit_guaranteed_pct,
        "death_benefit_total_20y_pct":   body.death_benefit_total_20y_pct,
        "cash_value_10y":                body.cash_value_10y,
        "cash_value_20y":                body.cash_value_20y,
        "audit_note":                    body.audit_note,
    }


@router.get("", response_model=List[WholeLifeProductOut], summary="终身寿险列表")
def list_whole_life(
    is_published: Optional[bool] = Query(None),
    insurer:      Optional[str]  = Query(None),
    limit:        int            = Query(50, ge=1, le=200),
    offset:       int            = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.product_type == ProductType.WHOLE_LIFE)
    if is_published is not None:
        q = q.filter(Product.is_published == is_published)
    if insurer:
        q = q.filter(Product.company.ilike(insurer))
    return [_to_out(p) for p in q.offset(offset).limit(limit).all()]


@router.get("/{product_code}", response_model=WholeLifeProductOut, summary="终身寿险详情")
def get_whole_life(product_code: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(
        Product.product_type == ProductType.WHOLE_LIFE,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    return _to_out(p)


@router.post("", response_model=WholeLifeProductOut, status_code=201, summary="新建终身寿险")
def create_whole_life(
    body: WholeLifeProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    if db.query(Product).filter(Product.slug == body.product_code).first():
        raise HTTPException(status_code=409, detail=f"product_code '{body.product_code}' 已存在")
    p = Product(product_type=ProductType.WHOLE_LIFE)
    _apply(p, body)
    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.put("/{product_code}", response_model=WholeLifeProductOut, summary="全量更新终身寿险")
def replace_whole_life(
    product_code: str,
    body: WholeLifeProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(
        Product.product_type == ProductType.WHOLE_LIFE,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    _apply(p, body)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.patch("/{product_code}", response_model=WholeLifeProductOut, summary="局部更新终身寿险")
def update_whole_life(
    product_code: str,
    body: WholeLifeProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(
        Product.product_type == ProductType.WHOLE_LIFE,
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
    json_fields = {"irr_30y", "non_guaranteed_ratio", "death_benefit_guaranteed_pct",
                   "death_benefit_total_20y_pct", "cash_value_10y", "cash_value_20y", "audit_note"}
    for k, v in patch.items():
        if k in field_map:
            setattr(p, field_map[k], v)
        elif k in json_fields:
            specs[k] = v
    p.specifications = specs
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.delete("/{product_code}", status_code=204, summary="删除终身寿险")
def delete_whole_life(
    product_code: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(
        Product.product_type == ProductType.WHOLE_LIFE,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    db.delete(p)
    db.commit()
