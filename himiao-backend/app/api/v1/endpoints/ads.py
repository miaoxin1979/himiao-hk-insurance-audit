"""
app/api/v1/endpoints/ads.py — 广告位管理

原代码错误地将 ads 逻辑混写在 brokers.py 中，且缺少必要的导入。
本文件将其独立出来，补齐所有导入。

公开接口：
  GET  /api/v1/ads                  → 获取当前激活广告位（前端调用）

管理接口（需要 JWT）：
  GET  /api/v1/ads/all              → 所有广告位列表（含未激活）
  POST /api/v1/ads                  → 新建广告位
  PATCH /api/v1/ads/{slot_key}      → 更新广告位内容/状态
  DELETE /api/v1/ads/{slot_key}     → 删除广告位
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.deps import get_db, require_editor, require_staff
from app.models.ad_slot import AdSlot
from app.models.user import User

router = APIRouter(prefix="/ads", tags=["Ads"])


class AdSlotCreate(BaseModel):
    slot_key:   str
    slot_name:  Optional[str]      = None
    ad_type:    str                = "banner"   # banner | native | text
    content:    Optional[str]      = None
    link_url:   Optional[str]      = None
    image_url:  Optional[str]      = None
    advertiser: Optional[str]      = None
    is_active:  bool               = False
    start_at:   Optional[datetime] = None
    end_at:     Optional[datetime] = None


class AdSlotUpdate(BaseModel):
    slot_name:  Optional[str]      = None
    ad_type:    Optional[str]      = None
    content:    Optional[str]      = None
    link_url:   Optional[str]      = None
    image_url:  Optional[str]      = None
    advertiser: Optional[str]      = None
    is_active:  Optional[bool]     = None
    start_at:   Optional[datetime] = None
    end_at:     Optional[datetime] = None


# ── 公开：当前激活广告位 ──────────────────────────────────────────
@router.get(
    "",
    summary="获取当前激活广告位",
    description="前端 Ticker / Sidebar 调用此接口拉取投放中的广告",
)
def list_active_ads(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    return db.query(AdSlot).filter(
        AdSlot.is_active == True,
    ).filter(
        (AdSlot.start_at == None) | (AdSlot.start_at <= now)
    ).filter(
        (AdSlot.end_at == None) | (AdSlot.end_at >= now)
    ).all()


# ── Admin：所有广告位列表 ──────────────────────────────────────────
@router.get(
    "/all",
    summary="[Admin] 所有广告位",
)
def list_all_ads(
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    return db.query(AdSlot).order_by(AdSlot.slot_key).all()


# ── Admin：新建广告位 ──────────────────────────────────────────────
@router.post("", status_code=201, summary="[Admin] 新建广告位")
def create_ad(
    body: AdSlotCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    if db.query(AdSlot).filter(AdSlot.slot_key == body.slot_key).first():
        raise HTTPException(400, f"slot_key 已存在: {body.slot_key}")
    slot = AdSlot(**body.model_dump())
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


# ── Admin：更新广告位 ──────────────────────────────────────────────
@router.patch(
    "/{slot_key}",
    summary="[Admin] 更新广告位内容或状态",
    description="上架: PATCH {is_active: true}  |  下架: PATCH {is_active: false}",
)
def update_ad(
    slot_key: str,
    body: AdSlotUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    slot = db.query(AdSlot).filter(AdSlot.slot_key == slot_key).first()
    if not slot:
        raise HTTPException(404, f"广告位不存在: {slot_key}")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(slot, k, v)
    db.commit()
    db.refresh(slot)
    return slot


# ── Admin：删除广告位 ──────────────────────────────────────────────
@router.delete("/{slot_key}", status_code=204, summary="[Admin] 删除广告位")
def delete_ad(
    slot_key: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    slot = db.query(AdSlot).filter(AdSlot.slot_key == slot_key).first()
    if not slot:
        raise HTTPException(404, f"广告位不存在: {slot_key}")
    db.delete(slot)
    db.commit()
