"""用户相关模式"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    status_tag: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """更新用户请求"""
    full_name: Optional[str] = None
    status_tag: Optional[str] = None
    is_active: Optional[bool] = None


class UserRoleUpdate(BaseModel):
    """更新用户角色请求（仅管理员）"""
    role: UserRole


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    items: list[UserResponse]
