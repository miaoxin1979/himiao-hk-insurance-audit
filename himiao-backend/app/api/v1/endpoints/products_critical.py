"""
app/api/v1/endpoints/products_critical.py
重疾险 CRUD — 读写真实 SQLite DB
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_editor
from app.models.product import Product, ProductType
from app.models.user import User
from app.models.products_typed import CriticalProductCreate, CriticalProductUpdate, CriticalProductOut

router = APIRouter(prefix="/products/critical_illness", tags=["Products · Critical Illness"])


def _to_out(p: Product) -> CriticalProductOut:
    specs = p.specifications or {}
    return CriticalProductOut(
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
        covered_conditions=p.covered_conditions_count,
        early_stage_conditions=specs.get("early_stage_conditions"),
        multipay_max_pct=specs.get("multipay_max_pct"),
        multipay_times=specs.get("multipay_times"),
        cancer_relapse_covered=specs.get("cancer_relapse_covered"),
        premium_waiver_on_claim=specs.get("premium_waiver_on_claim"),
        sum_assured_preserves=specs.get("sum_assured_preserves"),
        sum_assured_example=specs.get("sum_assured_example"),
        premium_example_annual=specs.get("premium_example_annual"),
        return_of_premium_year=specs.get("return_of_premium_year"),
    )


def _apply(p: Product, body: CriticalProductCreate) -> None:
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
    p.covered_conditions_count = body.covered_conditions
    p.multi_pay = True if (body.multipay_times and body.multipay_times > 1) else (
        False if body.multipay_times == 1 else None
    )
    p.specifications = {
        "early_stage_conditions":  body.early_stage_conditions,
        "multipay_max_pct":        body.multipay_max_pct,
        "multipay_times":          body.multipay_times,
        "cancer_relapse_covered":  body.cancer_relapse_covered,
        "premium_waiver_on_claim": body.premium_waiver_on_claim,
        "sum_assured_preserves":   body.sum_assured_preserves,
        "sum_assured_example":     body.sum_assured_example,
        "premium_example_annual":  body.premium_example_annual,
        "return_of_premium_year":  body.return_of_premium_year,
        "audit_note":              body.audit_note,
    }


@router.get("", response_model=List[CriticalProductOut], summary="重疾险列表")
def list_critical(
    is_published: Optional[bool] = Query(None),
    insurer:      Optional[str]  = Query(None),
    limit:        int            = Query(50, ge=1, le=200),
    offset:       int            = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Product).filter(Product.product_type == ProductType.CRITICAL_ILLNESS)
    if is_published is not None:
        q = q.filter(Product.is_published == is_published)
    if insurer:
        q = q.filter(Product.company.ilike(insurer))
    return [_to_out(p) for p in q.offset(offset).limit(limit).all()]


@router.get("/{product_code}", response_model=CriticalProductOut, summary="重疾险详情")
def get_critical(product_code: str, db: Session = Depends(get_db)):
    p = db.query(Product).filter(
        Product.product_type == ProductType.CRITICAL_ILLNESS,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    return _to_out(p)


@router.post("", response_model=CriticalProductOut, status_code=201, summary="新建重疾险")
def create_critical(
    body: CriticalProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    if db.query(Product).filter(Product.slug == body.product_code).first():
        raise HTTPException(status_code=409, detail=f"product_code '{body.product_code}' 已存在")
    p = Product(product_type=ProductType.CRITICAL_ILLNESS)
    _apply(p, body)
    db.add(p)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.put("/{product_code}", response_model=CriticalProductOut, summary="全量更新重疾险")
def replace_critical(
    product_code: str,
    body: CriticalProductCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(
        Product.product_type == ProductType.CRITICAL_ILLNESS,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    _apply(p, body)
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.patch("/{product_code}", response_model=CriticalProductOut, summary="局部更新重疾险")
def update_critical(
    product_code: str,
    body: CriticalProductUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(
        Product.product_type == ProductType.CRITICAL_ILLNESS,
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
        "covered_conditions": "covered_conditions_count",
    }
    json_fields = {"early_stage_conditions", "multipay_max_pct", "multipay_times",
                   "cancer_relapse_covered", "premium_waiver_on_claim", "sum_assured_preserves",
                   "sum_assured_example", "premium_example_annual", "return_of_premium_year", "audit_note"}
    for k, v in patch.items():
        if k in field_map:
            setattr(p, field_map[k], v)
        elif k in json_fields:
            specs[k] = v
    p.specifications = specs
    db.commit()
    db.refresh(p)
    return _to_out(p)


@router.delete("/{product_code}", status_code=204, summary="删除重疾险")
def delete_critical(
    product_code: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    p = db.query(Product).filter(
        Product.product_type == ProductType.CRITICAL_ILLNESS,
        Product.slug == product_code,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail=f"产品 {product_code} 不存在")
    db.delete(p)
    db.commit()
