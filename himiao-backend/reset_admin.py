#!/usr/bin/env python3
"""
════════════════════════════════════════════════════════════
  HiMiao Admin 密码急救脚本
  用法：在后端容器或 NAS 的后端目录下运行
  
  docker exec -it himiao-api python reset_admin.py
  或直接在后端目录：python reset_admin.py
════════════════════════════════════════════════════════════
"""
import sys
import os

# 允许在后端根目录或 backend/ 目录下运行
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from passlib.context import CryptContext
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    print(f"❌ 缺少依赖：{e}")
    print("   请先运行：pip install passlib[bcrypt] sqlalchemy")
    sys.exit(1)

# ── 配置 ──────────────────────────────────────────────────
# 必须显式提供 ADMIN_PASSWORD，避免默认弱口令进入公开仓库
NEW_PASSWORD = os.environ.get("ADMIN_PASSWORD")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME") or "admin"

# 优先环境变量（Docker Compose env_file 会注入），否则读后端目录 .env
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    DB_URL = "sqlite:///./himiao.db"
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        for line in open(env_path):
            line = line.strip()
            if line.startswith("DATABASE_URL="):
                DB_URL = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

print(f"📂 数据库：{DB_URL}")
print(f"👤 目标账号：{ADMIN_USERNAME}")
if not NEW_PASSWORD:
    print("❌ 缺少 ADMIN_PASSWORD 环境变量，已拒绝执行。")
    print("   例如：ADMIN_PASSWORD='your_strong_password' python reset_admin.py")
    sys.exit(1)
print("🔑 新密码：已接收（已隐藏）")
print()

# ── 生成 bcrypt hash ──────────────────────────────────────
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_ctx.hash(NEW_PASSWORD)
print(f"✅ bcrypt hash 已生成：{hashed[:30]}...")

# ── 连接数据库 ────────────────────────────────────────────
connect_args = {"check_same_thread": False} if "sqlite" in DB_URL else {}
engine = create_engine(DB_URL, connect_args=connect_args)
Session = sessionmaker(bind=engine)

with Session() as db:
    # 检查表是否存在
    result = db.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        if "sqlite" in DB_URL else
        "SELECT to_regclass('public.users')"
    )).fetchone()

    if not result:
        print("⚠️  users 表不存在，正在创建...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(128),
                hashed_pw VARCHAR(256) NOT NULL,
                role VARCHAR(32) DEFAULT 'admin',
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.commit()
        print("✅ users 表已创建")

    # 查找现有 admin
    existing = db.execute(
        text("SELECT id, username, hashed_pw, is_active FROM users WHERE username = :u"),
        {"u": ADMIN_USERNAME}
    ).fetchone()

    if existing:
        print(f"📋 找到现有账号 (id={existing[0]})，当前状态：{'激活' if existing[3] else '禁用'}")
        db.execute(
            text("UPDATE users SET hashed_pw = :h, is_active = TRUE WHERE username = :u"),
            {"h": hashed, "u": ADMIN_USERNAME}
        )
        db.commit()
        print("✅ 密码已重置（明文已隐藏）")
    else:
        print("📋 未找到 admin 账号，正在创建...")
        db.execute(
            text("""INSERT INTO users (username, hashed_pw, role, is_active)
                    VALUES (:u, :h, 'admin', TRUE)"""),
            {"u": ADMIN_USERNAME, "h": hashed}
        )
        db.commit()
        print(f"✅ Admin 账号已创建，用户名：{ADMIN_USERNAME}，密码：已隐藏")

    # 验证
    check = db.execute(
        text("SELECT id, username, role, is_active FROM users WHERE username = :u"),
        {"u": ADMIN_USERNAME}
    ).fetchone()
    print()
    print("═" * 50)
    print(f"✅ 验证完成：")
    print(f"   ID：{check[0]}")
    print(f"   用户名：{check[1]}")
    print(f"   角色：{check[2]}")
    print(f"   状态：{'激活 ✅' if check[3] else '禁用 ❌'}")
    print()

    # 顺便验证密码 hash 是否正确
    verify_ok = pwd_ctx.verify(NEW_PASSWORD, hashed)
    print(f"🔐 密码验证测试：{'通过 ✅' if verify_ok else '失败 ❌ — 请联系开发者'}")
    print("═" * 50)
    print()
    print("👉 现在可以用以下账号登录后台（密码已隐藏）：")
    print(f"   用户名：{ADMIN_USERNAME}")
    print("   密码：请使用你设置的 ADMIN_PASSWORD")
    print()
    print("⚠️  登录成功后请立即在后台修改密码！")
