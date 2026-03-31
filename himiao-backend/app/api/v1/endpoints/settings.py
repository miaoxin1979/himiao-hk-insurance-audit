"""
app/api/v1/endpoints/settings.py
──────────────────────────────────
站点设置接口（key-value 键值对）

路由：
  GET  /api/v1/settings        — 公开，返回全部设置 dict
  PUT  /api/v1/settings        — 需要 admin token，批量 upsert
"""
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_editor
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["Settings"])

# 建表 SQL（幂等，首次调用时执行）
_CREATE_TABLE_SQL = text("""
    CREATE TABLE IF NOT EXISTS site_settings (
        key   TEXT PRIMARY KEY,
        value TEXT
    )
""")


def _ensure_table(db: Session) -> None:
    """确保 site_settings 表存在（幂等）"""
    db.execute(_CREATE_TABLE_SQL)
    db.commit()


# ── GET /settings ─────────────────────────────────────────────────────────────
@router.get(
    "",
    summary="获取站点设置",
    description="公开接口，返回全部 key-value 配置，前端产品页可直接调用。",
    response_model=Dict[str, str],
)
def get_settings(db: Session = Depends(get_db)) -> Dict[str, str]:
    _ensure_table(db)
    rows = db.execute(text("SELECT key, value FROM site_settings")).fetchall()
    return {row[0]: (row[1] or "") for row in rows}


# ── PUT /settings ─────────────────────────────────────────────────────────────
@router.put(
    "",
    summary="批量更新站点设置",
    description="需要 admin JWT。接收 `{key: value}` dict，批量 upsert 到 site_settings 表。",
)
def upsert_settings(
    payload: Dict[str, str],
    db: Session = Depends(get_db),
    _: User = Depends(require_editor),
) -> Dict[str, bool]:
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请求体不能为空",
        )

    _ensure_table(db)

    try:
        for key, value in payload.items():
            db.execute(
                text("""
                    INSERT INTO site_settings (key, value)
                    VALUES (:key, :value)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """),
                {"key": key, "value": value},
            )
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"写入配置失败：{exc}",
        ) from exc

    return {"ok": True}
