#!/usr/bin/env python3
"""
后端服务启动脚本
用于直接运行Python启动服务（开发调试用）
"""
import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# 导入并运行uvicorn
if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
