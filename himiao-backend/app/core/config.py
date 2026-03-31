"""
app/core/config.py
统一配置对象——所有环境变量从这里读，业务代码不直接 os.getenv()
"""
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # ── 应用 ──
    APP_ENV: str = "development"
    APP_PORT: int = 8888
    CORS_ORIGINS: List[str] = ["http://localhost:8080"]

    # ── JWT ──
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # ── 数据库 ──
    # SQLite 本地 → 改这一行即可上云
    DATABASE_URL: str = "sqlite:////app/data/himiao.db"

    # ── Admin 初始账号 ──
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str

    # ── 文件存储 ──
    STORAGE_TYPE: str = "local"          # local | s3 | oss
    STORAGE_LOCAL_BASE: str = "/data/uploads"
    AWS_BUCKET: str = ""
    AWS_REGION: str = ""
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""

    # ── 邮件 ──
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = ""
    # SMTP（用于订阅通知，Outlook/Live 账号）
    SMTP_HOST: str = "smtp-mail.outlook.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""          # 填写 your_email@example.com
    SMTP_PASS: str = ""          # 填写邮箱密码
    NOTIFY_EMAIL: str = ""  # 新订阅通知接收邮箱

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"           # 允许 .env 有额外字段（如 MAC_IP, OLLAMA_MODEL_NAME）

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


# 全局单例
settings = Settings()
