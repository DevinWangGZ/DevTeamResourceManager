"""权限管理"""
from typing import List
from fastapi import Depends, HTTPException, status

from app.models.user import User, UserRole
from app.models.role import RoleType
from app.api.deps import get_current_user


def require_roles(allowed_roles: List[UserRole]):
    """角色权限检查装饰器工厂（向后兼容）"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """检查用户角色是否在允许的角色列表中"""
        allowed_role_codes = [role.value for role in allowed_roles]
        if not current_user.has_any_role(allowed_role_codes):
            role_names = ", ".join([role.value for role in allowed_roles])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {role_names}"
            )
        return current_user
    return role_checker


def require_role_codes(allowed_role_codes: List[str]):
    """角色权限检查装饰器工厂（使用角色代码）"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """检查用户角色是否在允许的角色列表中"""
        if not current_user.has_any_role(allowed_role_codes):
            role_names = ", ".join(allowed_role_codes)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {role_names}"
            )
        return current_user
    return role_checker


def get_current_developer(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前开发人员（开发人员及以上）"""
    return current_user


def get_current_project_manager(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前项目经理（项目经理及以上）"""
    allowed_role_codes = [
        RoleType.PROJECT_MANAGER.value,
        RoleType.DEVELOPMENT_LEAD.value,
        RoleType.SYSTEM_ADMIN.value
    ]
    if not current_user.has_any_role(allowed_role_codes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要项目经理权限"
        )
    return current_user


def get_current_development_lead(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前开发组长（开发组长及以上）"""
    allowed_role_codes = [
        RoleType.DEVELOPMENT_LEAD.value,
        RoleType.SYSTEM_ADMIN.value
    ]
    if not current_user.has_any_role(allowed_role_codes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要开发组长权限"
        )
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前系统管理员"""
    if not current_user.has_role(RoleType.SYSTEM_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要系统管理员权限"
        )
    return current_user


def check_user_permission(user: User, resource_user_id: int) -> bool:
    """检查用户是否有权限访问资源
    
    Args:
        user: 当前用户
        resource_user_id: 资源所属用户ID
    
    Returns:
        bool: 是否有权限
    """
    # 系统管理员可以访问所有资源
    if user.has_role(RoleType.SYSTEM_ADMIN.value):
        return True
    # 用户可以访问自己的资源
    if user.id == resource_user_id:
        return True
    # 开发组长可以访问开发人员的资源
    if user.has_role(RoleType.DEVELOPMENT_LEAD.value):
        # 这里可以添加更复杂的逻辑，比如检查resource_user是否是开发人员
        return True
    return False
