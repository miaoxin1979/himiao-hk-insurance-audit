"""
app/api/v1/endpoints/subscribers.py — 订阅者管理完整版 (M2)

接口清单：
  POST   /api/v1/subscribers            → 前端订阅表单（公开）
  GET    /api/v1/subscribers            → 订阅者列表，分页（JWT）
  GET    /api/v1/subscribers/export     → CSV 导出（JWT）
  DELETE /api/v1/subscribers/{sub_id}   → 软删除/退订（JWT）
"""
from __future__ import annotations

import csv
import io
import logging
import smtplib
import threading
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db, require_editor, require_staff
from app.models.subscriber import Subscriber
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscribers", tags=["Subscribers"])


def _send_notify(subscriber_email: str) -> None:
    """后台线程：新订阅时发通知邮件到 NOTIFY_EMAIL（静默失败）"""
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        return
    try:
        msg = MIMEText(
            f"新订阅者：{subscriber_email}\n时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "plain", "utf-8",
        )
        msg["Subject"] = f"[HiMiao] 新订阅 · {subscriber_email}"
        msg["From"] = settings.SMTP_USER
        msg["To"] = settings.NOTIFY_EMAIL
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
            smtp.sendmail(settings.SMTP_USER, [settings.NOTIFY_EMAIL], msg.as_string())
    except Exception as e:
        logger.warning("订阅通知邮件发送失败: %s", e)


# ── Schema ────────────────────────────────────────────────────────
class SubscribeIn(BaseModel):
    email:  EmailStr
    source: Optional[str] = "website"   # website | referral | campaign


# ── 公开：前端订阅表单 ────────────────────────────────────────────
@router.post("", status_code=201, summary="订阅（公开）")
def subscribe(body: SubscribeIn, db: Session = Depends(get_db)):
    """
    前端订阅表单调用。

    - 邮箱已存在且活跃：幂等返回成功
    - 邮箱已存在但已退订：重新激活
    - 新邮箱：正常创建
    """
    existing = db.query(Subscriber).filter(
        Subscriber.email == body.email
    ).first()

    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
        return {"message": "订阅成功"}

    s = Subscriber(email=body.email, source=body.source)
    db.add(s)
    db.commit()
    threading.Thread(target=_send_notify, args=(body.email,), daemon=True).start()
    return {"message": "订阅成功"}


# ── Admin：订阅者列表 ─────────────────────────────────────────────
@router.get("", summary="[Admin] 订阅者列表（分页）")
def list_subscribers(
    skip:      int           = Query(0),
    limit:     int           = Query(100, le=500),
    source:    Optional[str] = Query(None, description="来源筛选: website|referral|campaign"),
    is_active: Optional[bool] = Query(True, description="默认只看活跃订阅"),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    q = db.query(Subscriber)
    if is_active is not None:
        q = q.filter(Subscriber.is_active == is_active)
    if source:
        q = q.filter(Subscriber.source == source)
    total = q.count()
    items = q.order_by(Subscriber.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}


# ── Admin：CSV 导出 ───────────────────────────────────────────────
@router.get("/export", summary="[Admin] 导出订阅者 CSV")
def export_subscribers(
    is_active: Optional[bool] = Query(True),
    db: Session = Depends(get_db),
    _: User = Depends(require_staff),
):
    """
    导出订阅者列表为 CSV 文件，供邮件营销工具（Mailchimp / Resend 等）导入使用。
    默认只导出活跃订阅者。
    """
    q = db.query(Subscriber)
    if is_active is not None:
        q = q.filter(Subscriber.is_active == is_active)
    subscribers = q.order_by(Subscriber.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "email", "source", "is_active", "created_at"])
    for s in subscribers:
        writer.writerow([
            s.id,
            s.email,
            s.source or "website",
            s.is_active,
            s.created_at.isoformat() if s.created_at else "",
        ])

    output.seek(0)
    filename = f"subscribers_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Admin：删除订阅者（软删除）────────────────────────────────────
@router.delete("/{sub_id}", status_code=204, summary="[Admin] 退订/删除")
def delete_subscriber(
    sub_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
):
    s = db.query(Subscriber).filter(Subscriber.id == sub_id).first()
    if not s:
        raise HTTPException(404, "订阅者不存在")
    s.is_active = False
    db.commit()
