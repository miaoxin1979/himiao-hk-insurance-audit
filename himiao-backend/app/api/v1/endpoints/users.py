"""
app/api/v1/endpoints/users.py
仅超级管理员（role=admin）可管理后台用户。
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_super_admin
from app.core.security import hash_password
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

ALLOWED_ROLES = frozenset({"admin", "editor", "viewer"})


class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=8, description="至少 8 位")
    role: str = Field(..., description="admin | editor | viewer")
    email: Optional[str] = Field(None, max_length=128)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        v = v.strip()
        if v not in ALLOWED_ROLES:
            raise ValueError(f"role 必须是 {', '.join(sorted(ALLOWED_ROLES))}")
        return v


class UserPatch(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    email: Optional[str] = Field(None, max_length=128)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if v not in ALLOWED_ROLES:
            raise ValueError(f"role 必须是 {', '.join(sorted(ALLOWED_ROLES))}")
        return v


class PasswordResetBody(BaseModel):
    new_password: str = Field(..., min_length=8)


def _count_admins(db: Session) -> int:
    return (
        db.query(User)
        .filter(User.role == "admin", User.is_active == True)  # noqa: E712
        .count()
    )


def _ensure_not_last_admin(
    db: Session,
    target: User,
    *,
    new_role: Optional[str] = None,
    deactivate: bool = False,
) -> None:
    """保证至少保留一名激活的 admin。"""
    if target.role != "admin" or not target.is_active:
        return
    admin_count = _count_admins(db)
    if admin_count <= 1:
        if deactivate or (new_role is not None and new_role != "admin"):
            raise HTTPException(
                status_code=400,
                detail="不能移除唯一的超级管理员，请先创建另一名管理员或转移角色",
            )


@router.get("", summary="[超级管理员] 用户列表")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
) -> List[UserOut]:
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserOut.model_validate(u) for u in users]


@router.post("", status_code=201, summary="[超级管理员] 新建用户")
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    un = body.username.strip()
    if db.query(User).filter(User.username == un).first():
        raise HTTPException(400, "用户名已存在")

    if body.email:
        if db.query(User).filter(User.email == body.email.strip()).first():
            raise HTTPException(400, "该邮箱已被使用")

    u = User(
        username=un,
        email=body.email.strip() if body.email else None,
        hashed_pw=hash_password(body.password),
        role=body.role,
        is_active=True,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return UserOut.model_validate(u)


@router.patch("/{user_id}", summary="[超级管理员] 更新用户（角色/状态/邮箱）")
def patch_user(
    user_id: int,
    body: UserPatch,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "用户不存在")

    if body.role is not None:
        _ensure_not_last_admin(db, u, new_role=body.role)
        u.role = body.role

    if body.is_active is not None:
        if body.is_active is False:
            _ensure_not_last_admin(db, u, deactivate=True)
        u.is_active = body.is_active

    if body.email is not None:
        em = body.email.strip() if body.email else None
        if em:
            ex = (
                db.query(User)
                .filter(User.email == em, User.id != user_id)
                .first()
            )
            if ex:
                raise HTTPException(400, "该邮箱已被使用")
        u.email = em

    db.commit()
    db.refresh(u)
    return UserOut.model_validate(u)


@router.patch("/{user_id}/password", summary="[超级管理员] 重置用户密码")
def reset_password(
    user_id: int,
    body: PasswordResetBody,
    db: Session = Depends(get_db),
    _: User = Depends(require_super_admin),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "用户不存在")
    u.hashed_pw = hash_password(body.new_password)
    db.commit()
    return {"message": "密码已更新"}


@router.delete("/{user_id}", status_code=204, summary="[超级管理员] 删除用户")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_super_admin),
):
    if user_id == current.id:
        raise HTTPException(400, "不能删除当前登录账号")

    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "用户不存在")

    _ensure_not_last_admin(db, u, deactivate=True)

    db.delete(u)
    db.commit()
    return None
