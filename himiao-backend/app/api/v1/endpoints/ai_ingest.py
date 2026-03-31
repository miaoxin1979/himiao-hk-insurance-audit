"""
app/api/v1/endpoints/ai_ingest.py
──────────────────────────────────
AI 解析 + 自动入库 API

端点：
  GET  /api/v1/ai/health          — 检查 Ollama 状态
  POST /api/v1/ai/parse           — PDF/产品名 → Ollama 解析 → 去重 → 入库
  POST /api/v1/ai/ingest          — 直接提交已解析 JSON → 去重 → 入库（跳过 AI）

权限：所有写操作需要 admin token
"""
from __future__ import annotations

from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_editor
from app.models.user import User
from app.services.ai_parser import parse_product_with_ollama, check_ollama_health
from app.services.ingest import ingest_parsed_product

router = APIRouter(prefix="/ai", tags=["AI · 解析与入库"])


# ── Request / Response 模型 ──────────────────────────────────────────

class ParseRequest(BaseModel):
    insurer:      str           = Field(...,        description="保司简称，如 AIA")
    product_name: str           = Field(...,        description="产品名称，如 充裕未来III")
    product_type: str           = Field("savings",  description="savings | whole_life | critical_illness")
    pdf_url:      Optional[str] = Field(None,       description="保司官方 PDF 链接（可选，有则优先从中提取数据）")


class IngestRequest(BaseModel):
    """直接提交已解析的产品 JSON，跳过 AI 步骤（用于人工修正后重入库）"""
    product_type: str  = Field("savings",  description="savings | whole_life | critical_illness")
    parsed_data:  dict = Field(...,        description="符合 ai_parser 输出格式的产品 JSON")


class IngestResult(BaseModel):
    status:       str
    action:       str            # "created" | "updated"
    product_code: str
    id:           int
    parsed_fields: Optional[dict[str, Any]] = None


# ── 端点 ──────────────────────────────────────────────────────────────

@router.get("/health", summary="检查 Ollama 状态")
async def ollama_health():
    """返回 Ollama 在线状态、可用模型列表及目标模型是否就绪。"""
    return await check_ollama_health()


@router.post("/parse", response_model=IngestResult, summary="AI 解析 + 自动入库")
async def parse_and_ingest(
    req: ParseRequest,
    db:  Session = Depends(get_db),
    _:   User    = Depends(require_editor),
):
    """
    完整流程：
    1. 若有 pdf_url → 下载并提取文字
    2. 调用 Ollama 推理（deepseek-r1:32b）提取精算字段
    3. 去重：同险种 + 保司 + 产品名比对现有 DB
       - 命中 → UPDATE（只更新非 null 字段）
       - 未命中 → INSERT 草稿（is_published=False）
    4. 返回 action(created/updated) + product_code
    """
    try:
        parsed = await parse_product_with_ollama(
            insurer=req.insurer,
            product_name=req.product_name,
            product_type=req.product_type,
            pdf_url=req.pdf_url,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        result = ingest_parsed_product(db, parsed)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 返回时过滤掉 specifications（太长），只返回 top-level 字段
    preview = {k: v for k, v in parsed.items() if k != "specifications"}

    return IngestResult(
        status="ok",
        action=result["action"],
        product_code=result["product_code"],
        id=result["id"],
        parsed_fields=preview,
    )


@router.post("/ingest", response_model=IngestResult, summary="直接入库（跳过 AI）")
async def ingest_direct(
    req: IngestRequest,
    db:  Session = Depends(get_db),
    _:   User    = Depends(require_editor),
):
    """
    将已解析好的产品 JSON 直接去重入库。
    适用场景：
    - 人工修正 AI 输出后重新提交
    - 批量导入历史数据
    """
    data = dict(req.parsed_data)
    data["product_type"] = req.product_type

    try:
        result = ingest_parsed_product(db, data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return IngestResult(
        status="ok",
        action=result["action"],
        product_code=result["product_code"],
        id=result["id"],
    )
