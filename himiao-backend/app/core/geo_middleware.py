"""
app/core/geo_middleware.py
V8.0 Geo-IP 边缘拦截中间件

Phase 1 (NAS MVP)：仅记录日志，不硬拦截
Phase 2 (Cloudflare)：Cloudflare Worker 透传 CF-IPCountry header，后端据此拦截

受保护的敏感接口：/api/v1/pdf/* 等下载类接口
"""
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# 受 Geo 限制的接口前缀
GEO_RESTRICTED_PATHS = [
    "/api/v1/pdf/",
    "/api/v1/reports/",
    "/api/v1/subscribe",   # 留资接口
]

# 内地区域代码（Cloudflare CF-IPCountry header 格式）
MAINLAND_CHINA_CODE = "CN"


async def geo_block_middleware(request: Request, call_next):
    """
    Cloudflare Workers 边缘拦截预留中间件
    Phase 1：CF-IPCountry header 不存在时跳过（NAS 直连无此 header）
    Phase 2：Cloudflare 上线后自动生效
    """
    path = request.url.path
    is_restricted = any(path.startswith(p) for p in GEO_RESTRICTED_PATHS)

    if is_restricted:
        # Cloudflare 透传的国家代码
        cf_country = request.headers.get("CF-IPCountry", "")

        if cf_country == MAINLAND_CHINA_CODE:
            logger.warning(f"Geo-block: CN IP attempted {path}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "geo_restricted",
                    "message": (
                        "本平台仅提供公开精算数据模型展示，"
                        "不面向中国内地提供推介或下载服务。"
                        " | This service is not available in Mainland China."
                    )
                }
            )

    return await call_next(request)
