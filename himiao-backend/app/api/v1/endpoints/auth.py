"""
app/api/v1/endpoints/auth.py
────────────────────────────
路由：
  POST /api/v1/auth/login
  POST /api/v1/auth/change-password   ← 新增
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import STAFF_ROLES, get_db, require_editor, require_staff
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Schemas ──────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8,
                              description="新密码不少于 8 位")


# ── POST /auth/login ──────────────────────────────────────────────────────────
@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已停用",
        )
    if user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="该账号无权登录后台",
        )
    token = create_access_token(user.username, user.role)
    return {"access_token": token, "token_type": "bearer"}


# ── GET /auth/me ──────────────────────────────────────────────────────────────
class MeOut(BaseModel):
    username: str
    role: str
    email: Optional[str] = None


@router.get("/me", summary="当前登录用户信息（JWT）")
def me(current_user: User = Depends(require_staff)):
    return MeOut(
        username=current_user.username,
        role=current_user.role,
        email=current_user.email,
    )


# ── POST /auth/change-password ────────────────────────────────────────────────
@router.post(
    "/change-password",
    summary="修改管理员密码",
    description="""
    修改密码三步流程：
    1. bcrypt 验证 old_password
    2. bcrypt rehash new_password → 写入 DB
    3. 返回 action=re-login，前端清除 JWT 并跳转登录页
    """,
)
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor),
):
    # 1. 验证旧密码
    if not verify_password(body.old_password, current_user.hashed_pw):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码不正确",
        )

    # 2. 哈希新密码并写库
    current_user.hashed_pw = hash_password(body.new_password)
    db.commit()

    # 3. 通知前端重新登录
    return {"message": "密码已修改，请重新登录", "action": "re-login"}
