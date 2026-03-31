"""
app/api/v1/endpoints/brokers.py — 经纪人完整 CRUD (M2)

接口清单：
  GET    /api/v1/brokers                 → 已认证经纪人列表（公开）
  GET    /api/v1/brokers/admin/all       → 全部经纪人含未认证（JWT）
  GET    /api/v1/brokers/{broker_id}     → 单个经纪人（公开）
  POST   /api/v1/brokers                 → 新建（JWT）
  PATCH  /api/v1/brokers/{broker_id}     → 更新信息（JWT）
  PATCH  /api/v1/brokers/{broker_id}/verify   → 标记已认证（JWT）
  PATCH  /api/v1/brokers/{broker_id}/unverify → 取消认证（JWT）
  DELETE /api/v1/brokers/{broker_id}     → 软删除（JWT）
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_editor, require_staff
from app.models.broker import Broker
from app.models.user import User

router = APIRouter(prefix="/brokers", tags=["Brokers"])


# ── Schemas ───────────────────────────────────────────────────────
class BrokerCreate(BaseModel):
    name:        str
    license_no:  Optional[str]   = None   # 香港保监局牌照号
    company:     Optional[str]   = None
    phone:       Optional[str]   = None
    email:       Optional[str]   = None
    wechat:      Optional[str]   = None
    intro:       Optional[str]   = None
    avatar_url:  Optional[str]   = None
    specialties: Optional[str]   = None   # 逗号分隔: "储蓄险,重疾险"


class BrokerPatch(BaseModel):
    """PATCH 语义：所有字段可选"""
    name:        Optional[str]   = None
    license_no:  Optional[str]   = None
    company:     Optional[str]   = None
    phone:       Optional[str]   = None
    email:       Optional[str]   = None
    wechat:      Optional[str]   = None
    intro:       Optional[str]   = None
    avatar_url:  Optional[str]   = None
    specialties: Optional[str]   = None
    rating:      Optional[float] = None


# ── 公开：已认证经纪人列表 ────────────────────────────────────────
@router.get("", summary="已认证经纪人列表（公开）")
def list_brokers(
    specialty:     Optional[str] = Query(None, description="按专长筛选，如: 储蓄险"),
    verified_only: bool          = Query(True,  description="仅返回已认证经纪人"),
    db: Session = Depends(get_db),
):
    q = db.query(Broker).filter(Broker.is_active == True)
    if verified_only:
        q = q.filter(Broker.is_verified == True)
    if specialty:
        q = q.filter(Broker.specialties.contains(specialty))
    return q.order_by(Broker.rating.desc()).all()


# ── Admin：全部经纪人（含未认证）────────────────────────────────
@router.get("/admin/all", summary="[Admin] 全部经纪人含未认证")
def admin_list_all(
    is_verified: Optional[bool] = Query(None),
    skip:        int            = Query(0),
    limit:       int            = Query(100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    q = db.query(Broker).filter(Broker.is_active == True)
    if is_verified is not None:
        q = q.filter(Broker.is_verified == is_verified)
    total = q.count()
    items = q.order_by(Broker.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


# ── 公开：单个经纪人 ──────────────────────────────────────────────
@router.get("/{broker_id}", summary="单个经纪人详情（公开）")
def get_broker(broker_id: int, db: Session = Depends(get_db)):
    b = db.query(Broker).filter(
        Broker.id == broker_id,
        Broker.is_active == True,
    ).first()
    if not b:
        raise HTTPException(404, "经纪人不存在")
    return b


# ── Admin：新建经纪人 ─────────────────────────────────────────────
@router.post("", status_code=201, summary="[Admin] 新建经纪人")
def create_broker(
    body: BrokerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    """
    新建经纪人。默认 is_verified=False，需管理员手动认证后才对外展示。
    """
    b = Broker(**body.model_dump())
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


# ── Admin：更新经纪人信息 ─────────────────────────────────────────
@router.patch("/{broker_id}", summary="[Admin] 更新经纪人信息")
def patch_broker(
    broker_id: int,
    body: BrokerPatch,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    b = db.query(Broker).filter(Broker.id == broker_id).first()
    if not b:
        raise HTTPException(404, "经纪人不存在")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    db.commit()
    db.refresh(b)
    return b


# ── Admin：认证经纪人 ─────────────────────────────────────────────
@router.patch("/{broker_id}/verify", summary="[Admin] 标记已认证")
def verify_broker(
    broker_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    b = db.query(Broker).filter(Broker.id == broker_id).first()
    if not b:
        raise HTTPException(404, "经纪人不存在")
    b.is_verified = True
    db.commit()
    return {"id": b.id, "name": b.name, "is_verified": True}


# ── Admin：取消认证 ───────────────────────────────────────────────
@router.patch("/{broker_id}/unverify", summary="[Admin] 取消认证")
def unverify_broker(
    broker_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    b = db.query(Broker).filter(Broker.id == broker_id).first()
    if not b:
        raise HTTPException(404, "经纪人不存在")
    b.is_verified = False
    db.commit()
    return {"id": b.id, "name": b.name, "is_verified": False}


# ── Admin：软删除 ─────────────────────────────────────────────────
@router.delete("/{broker_id}", status_code=204, summary="[Admin] 删除经纪人（软删除）")
def delete_broker(
    broker_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    b = db.query(Broker).filter(Broker.id == broker_id).first()
    if not b:
        raise HTTPException(404, "经纪人不存在")
    b.is_active = False
    db.commit()
