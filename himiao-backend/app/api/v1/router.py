"""
app/api/v1/router.py — v1 路由总汇
"""
from fastapi import APIRouter
from app.api.v1.endpoints.auth               import router as auth_router
from app.api.v1.endpoints.products           import router as products_router
from app.api.v1.endpoints.articles           import router as articles_router
from app.api.v1.endpoints.subscribers        import router as subscribers_router
from app.api.v1.endpoints.brokers            import router as brokers_router
from app.api.v1.endpoints.ads                import router as ads_router
from app.api.v1.endpoints.settings           import router as settings_router
from app.api.v1.endpoints.users              import router as users_router
from app.api.v1.endpoints.upload             import router as upload_router

# ── 三大险种 CRUD ───────────────────────────────────────────────────
from app.api.v1.endpoints.products_savings    import router as savings_router
from app.api.v1.endpoints.products_whole_life import router as whole_life_router
from app.api.v1.endpoints.products_critical   import router as critical_router
from app.api.v1.endpoints.ai_ingest           import router as ai_ingest_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(upload_router)
api_router.include_router(ai_ingest_router)          # AI 解析与入库
# 三大险种具体路由必须在通用 /products/{slug} 之前注册，否则被拦截
api_router.include_router(savings_router)
api_router.include_router(whole_life_router)
api_router.include_router(critical_router)
api_router.include_router(products_router)
api_router.include_router(articles_router)
api_router.include_router(subscribers_router)
api_router.include_router(brokers_router)
api_router.include_router(ads_router)
api_router.include_router(settings_router)           # 站点设置
api_router.include_router(users_router)              # 用户管理（仅超级管理员）
