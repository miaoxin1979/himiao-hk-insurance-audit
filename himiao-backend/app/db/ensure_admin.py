"""
首次部署 / 空库时：根据 .env 的 ADMIN_USERNAME、ADMIN_PASSWORD 创建管理员账号。
登录接口只校验数据库 users 表，不会读取 .env 密码 —— 若从未写入 users，将出现「用户名密码错误」。
"""
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User

log = logging.getLogger(__name__)


def ensure_default_admin_user(db: Session) -> None:
    """若不存在 ADMIN_USERNAME 对应用户，则创建（不覆盖已有密码）。"""
    un = settings.ADMIN_USERNAME.strip()
    if not un or not settings.ADMIN_PASSWORD:
        log.warning("ensure_default_admin_user: 跳过（ADMIN_USERNAME 或 ADMIN_PASSWORD 为空）")
        return

    existing = db.query(User).filter(User.username == un).first()
    if existing:
        return

    user = User(
        username=un,
        email=None,
        hashed_pw=hash_password(settings.ADMIN_PASSWORD),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    log.info("已创建默认管理员账号：%s（请在登录后尽快修改密码）", un)
