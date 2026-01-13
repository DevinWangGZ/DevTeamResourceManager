#!/usr/bin/env python
"""初始化数据库脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import engine
from app.models.base import Base

def init_db():
    """初始化数据库表"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")

if __name__ == "__main__":
    init_db()
