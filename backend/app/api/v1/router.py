"""API路由聚合"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth

api_router = APIRouter()

# 注册路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
# api_router.include_router(users.router, prefix="/users", tags=["用户"])
# api_router.include_router(tasks.router, prefix="/tasks", tags=["任务"])
