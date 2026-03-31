"""
app/db/session.py
SQLAlchemy engine + SessionLocal
DATABASE_URL 驱动：sqlite → postgresql 零代码切换
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# SQLite 需要开启 WAL 模式（解决并发读写锁问题）
# PostgreSQL 不需要此配置，条件判断自动跳过
connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,         # 自动重连（对 PostgreSQL 重要）
    echo=(settings.APP_ENV == "development"),  # dev 模式打印 SQL
)

# SQLite 专属优化：WAL 日志模式提升并发性能
if settings.is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
