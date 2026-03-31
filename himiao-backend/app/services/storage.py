"""
app/services/storage.py
文件存储抽象层：本地 → S3/OSS 无缝切换
"""
import os
import shutil
from pathlib import Path
from app.core.config import settings


def save_file(file_bytes: bytes, filename: str) -> str:
    """
    保存文件，返回可访问的相对路径
    STORAGE_TYPE=local  → 写入本地路径
    STORAGE_TYPE=s3     → 上传 AWS S3（上云时实现）
    STORAGE_TYPE=oss    → 上传阿里云 OSS（上云时实现）
    """
    if settings.STORAGE_TYPE == "local":
        return _save_local(file_bytes, filename)
    elif settings.STORAGE_TYPE == "s3":
        return _save_s3(file_bytes, filename)
    elif settings.STORAGE_TYPE == "oss":
        return _save_oss(file_bytes, filename)
    raise ValueError(f"Unknown STORAGE_TYPE: {settings.STORAGE_TYPE}")


def _save_local(file_bytes: bytes, filename: str) -> str:
    base = Path(settings.STORAGE_LOCAL_BASE)
    base.mkdir(parents=True, exist_ok=True)
    dest = base / filename
    dest.write_bytes(file_bytes)
    return f"/uploads/{filename}"


def _save_s3(file_bytes: bytes, filename: str) -> str:
    # TODO: Phase 3 上云时实现
    # import boto3
    # s3 = boto3.client('s3', ...)
    # s3.put_object(Bucket=settings.AWS_BUCKET, Key=filename, Body=file_bytes)
    # return f"https://{settings.AWS_BUCKET}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
    raise NotImplementedError("S3 storage not yet configured")


def _save_oss(file_bytes: bytes, filename: str) -> str:
    # TODO: 阿里云 OSS
    raise NotImplementedError("OSS storage not yet configured")
