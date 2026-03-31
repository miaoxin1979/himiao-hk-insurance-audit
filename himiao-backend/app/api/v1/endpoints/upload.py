"""图片上传（讲堂富文本等）"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.deps import require_editor
from app.models.user import User
from app.services.storage import save_file

router = APIRouter(prefix="/upload", tags=["Upload"])

_ALLOWED = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}


@router.post("/image", summary="[Admin] 上传图片，返回可嵌入正文的 URL")
async def upload_image(
    file: UploadFile = File(...),
    _: User = Depends(require_editor),
):
    if not file.content_type or file.content_type not in _ALLOWED:
        raise HTTPException(400, "请上传 JPG / PNG / WebP / GIF 图片")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(400, "图片过大（最大 5MB）")
    ext = _ALLOWED[file.content_type]
    name = f"img_{uuid.uuid4().hex[:16]}.{ext}"
    path = save_file(data, name)
    return {"ok": True, "url": path}
