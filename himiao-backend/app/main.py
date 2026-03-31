import json
import os
import secrets

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.v1.router import api_router
from app.core.config import settings

_DOCS_USER = os.getenv("DOCS_USER", "himiao_admin")
_DOCS_PASS = os.getenv("DOCS_PASS", "CHANGE_THIS_NOW")

app = FastAPI(
    title="HiMiao Audit API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

try:
    _origins = json.loads(os.getenv("CORS_ORIGINS", '["*"]'))
except Exception:
    _origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(api_router)

# 本地图片上传静态访问（与 /upload/image 返回的 /uploads/... 对应）
_uploads_dir = Path(settings.STORAGE_LOCAL_BASE)
_uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(_uploads_dir)), name="uploads")


@app.on_event("startup")
def _run_migrations():
    """安全加列 migration — 幂等，列已存在时静默跳过"""
    from sqlalchemy import text
    from app.db.session import engine

    # 需要幂等执行的 ALTER 语句（列已存在时 SQLite 会报错，直接吞掉）
    alter_migrations = [
        "ALTER TABLE articles ADD COLUMN source_url TEXT",
        "ALTER TABLE articles ADD COLUMN channel TEXT",
        "ALTER TABLE articles ADD COLUMN content_format TEXT",
    ]

    # 需要确保存在的新表
    create_migrations = [
        """
        CREATE TABLE IF NOT EXISTS site_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
        """,
    ]

    with engine.connect() as conn:
        # ALTER 类：忽略"列已存在"错误
        for sql in alter_migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                pass  # 列已存在或 DB 不支持，忽略

        # CREATE IF NOT EXISTS 类：直接执行，天然幂等
        for sql in create_migrations:
            conn.execute(text(sql))
            conn.commit()

        for upd in (
            "UPDATE articles SET channel = 'news' WHERE channel IS NULL OR channel = ''",
            "UPDATE articles SET content_format = 'markdown' WHERE content_format IS NULL OR content_format = ''",
        ):
            try:
                conn.execute(text(upd))
                conn.commit()
            except Exception:
                pass

    # 保司评级表 + 自动种子（部署到 NAS 等环境时无需手动执行）
    from app.db.base import Base
    from app.db.session import SessionLocal
    from app.db.seed_ratings import seed_insurer_ratings
    Base.metadata.create_all(bind=engine)
    try:
        db = SessionLocal()
        try:
            from app.db.ensure_admin import ensure_default_admin_user
            ensure_default_admin_user(db)
        except Exception:
            pass  # 用户表异常时不阻塞启动
        seed_insurer_ratings(db)
        try:
            from app.db.seed_academy import seed_academy_articles

            seed_academy_articles(db)
        except Exception:
            pass
        db.close()
    except Exception:
        pass  # 表被锁等异常时静默跳过，不影响启动


_basic = HTTPBasic()

def _verify_docs_auth(creds: HTTPBasicCredentials = Depends(_basic)):
    ok_user = secrets.compare_digest(
        creds.username.encode(), _DOCS_USER.encode()
    )
    ok_pass = secrets.compare_digest(
        creds.password.encode(), _DOCS_PASS.encode()
    )
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="口文档：凭证错误",
            headers={"WWW-Authenticate": "Basic realm='HiMiao Docs'"},
        )
    return creds

@app.get("/docs", include_in_schema=False)
async def _docs(creds: HTTPBasicCredentials = Depends(_verify_docs_auth)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{app.title} · Swagger UI")

@app.get("/redoc", include_in_schema=False)
async def _redoc(creds: HTTPBasicCredentials = Depends(_verify_docs_auth)):
    return get_redoc_html(openapi_url="/openapi.json", title=f"{app.title} · ReDoc")

@app.get("/openapi.json", include_in_schema=False)
async def _openapi(creds: HTTPBasicCredentials = Depends(_verify_docs_auth)):
    return JSONResponse(get_openapi(title=app.title, version=app.version, routes=app.routes))

@app.get("/health", include_in_schema=False)
async def _health():
    return {"status": "ok"}
