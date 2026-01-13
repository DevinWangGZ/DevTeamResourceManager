"""通用模式"""
from pydantic import BaseModel


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
