"""API路由聚合"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, tasks, skills, experiences, user_sequences, workload_statistics

api_router = APIRouter()

# 注册路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(skills.router, prefix="/skills", tags=["技能管理"])
api_router.include_router(experiences.router, prefix="/experiences", tags=["业务履历管理"])
api_router.include_router(user_sequences.router, prefix="/user-sequences", tags=["序列管理"])
api_router.include_router(workload_statistics.router, prefix="/workload-statistics", tags=["工作量统计"])