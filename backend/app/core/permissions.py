"""权限管理"""
from typing import List
from fastapi import Depends, HTTPException, status

from app.models.user import User, UserRole
from app.api.deps import get_current_user


def require_roles(allowed_roles: List[UserRole]):
    """角色权限检查装饰器工厂"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """检查用户角色是否在允许的角色列表中"""
        user_role = UserRole(current_user.role)
        if user_role not in allowed_roles:
            role_names = ", ".join([role.value for role in allowed_roles])
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
    user_role = UserRole(current_user.role)
    allowed_roles = [
        UserRole.PROJECT_MANAGER,
        UserRole.DEVELOPMENT_LEAD,
        UserRole.SYSTEM_ADMIN
    ]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要项目经理权限"
        )
    return current_user


def get_current_development_lead(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前开发组长（开发组长及以上）"""
    user_role = UserRole(current_user.role)
    allowed_roles = [
        UserRole.DEVELOPMENT_LEAD,
        UserRole.SYSTEM_ADMIN
    ]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要开发组长权限"
        )
    return current_user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前系统管理员"""
    user_role = UserRole(current_user.role)
    if user_role != UserRole.SYSTEM_ADMIN:
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
    user_role = UserRole(user.role)
    # 系统管理员可以访问所有资源
    if user_role == UserRole.SYSTEM_ADMIN:
        return True
    # 用户可以访问自己的资源
    if user.id == resource_user_id:
        return True
    # 开发组长可以访问开发人员的资源
    if user_role == UserRole.DEVELOPMENT_LEAD:
        # 这里可以添加更复杂的逻辑，比如检查resource_user是否是开发人员
        return True
    return False
