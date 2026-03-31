"""
app/core/deps.py
FastAPI 依赖注入
  - get_db       → 数据库 session（自动关闭）
  - get_current_user → JWT 验证，返回当前 admin 用户
  - require_admin → 角色校验（admin only）
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.security import decode_token
from app.models.user import User

bearer_scheme = HTTPBearer()


def get_db() -> Generator:
    """提供数据库 session，请求结束自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """验证 Bearer Token，返回当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token 无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(credentials.credentials)
    if not payload:
        raise credentials_exception

    username: str = payload.get("sub")
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user:
        raise credentials_exception
    return user


# 后台可登录角色：超级管理员 / 编辑 / 只读
STAFF_ROLES = frozenset({"admin", "editor", "viewer"})
# 可改数据（非只读）
EDITOR_ROLES = frozenset({"admin", "editor"})


def require_staff(current_user: User = Depends(get_current_user)) -> User:
    """可登录后台（含只读 viewer）"""
    if current_user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="后台权限不足")
    return current_user


def require_editor(current_user: User = Depends(get_current_user)) -> User:
    """编辑及以上（禁止只读账号执行写入）"""
    if current_user.role not in EDITOR_ROLES:
        raise HTTPException(
            status_code=403,
            detail="需要编辑权限（当前账号为只读）",
        )
    return current_user


def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """仅超级管理员：用户管理、角色分配"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """兼容旧代码：与 require_staff 相同"""
    return require_staff(current_user)
