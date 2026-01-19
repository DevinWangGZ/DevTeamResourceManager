"""用户相关模式"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from app.models.user import UserRole


class RoleResponse(BaseModel):
    """角色响应"""
    id: int
    name: str
    code: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: Optional[str] = None  # 向后兼容，已废弃
    roles: List[RoleResponse] = []  # 用户角色列表
    role_codes: List[str] = []  # 角色代码列表（便于前端使用）
    status_tag: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True

    @classmethod
    def from_user(cls, user):
        """从User对象创建UserResponse"""
        roles = list(user.roles) if hasattr(user, 'roles') and user.roles else []
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,  # 向后兼容
            roles=[RoleResponse.model_validate(role) for role in roles],
            role_codes=[role.code for role in roles],
            status_tag=user.status_tag,
            is_active=user.is_active,
        )


class UserUpdate(BaseModel):
    """更新用户请求"""
    full_name: Optional[str] = None
    status_tag: Optional[str] = None
    is_active: Optional[bool] = None


class UserRoleUpdate(BaseModel):
    """更新用户角色请求（仅管理员，向后兼容）"""
    role: UserRole


class UserRolesUpdate(BaseModel):
    """更新用户角色列表请求（仅管理员）"""
    role_codes: List[str]


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    items: list[UserResponse]


class UserCreate(BaseModel):
    """创建用户请求（仅管理员）"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role_codes: List[str] = []  # 角色代码列表，默认为空（将创建为开发人员）
    is_active: bool = True
