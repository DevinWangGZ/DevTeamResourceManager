"""认证相关模式"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


class Token(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据"""
    user_id: Optional[int] = None


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str
    password: str


class UserRegister(BaseModel):
    """用户注册请求"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


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


class UserCreate(BaseModel):
    """创建用户请求"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.DEVELOPER
    status_tag: Optional[str] = None
