"""数据库会话管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# 数据库连接参数
connect_args = {}
if settings.USE_SQLITE:
    connect_args = {"check_same_thread": False}
elif settings.DATABASE_TYPE == "mysql":
    # MySQL连接参数
    connect_args = {
        "charset": "utf8mb4",
        "connect_timeout": 10,
    }

# 创建数据库引擎
# MySQL需要设置echo_pool=True来查看连接池状态（可选）
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,  # 连接前ping，确保连接有效
    pool_recycle=3600,   # 连接回收时间（秒）
    echo=False,          # 是否打印SQL（开发时可设为True）
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
