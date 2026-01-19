"""用户服务"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.role import Role, RoleType
from app.schemas.user import UserUpdate, UserRoleUpdate, UserCreate
from app.services.role_service import RoleService
from app.services.auth_service import create_user
from app.core.config import settings


def get_user(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户（包含角色信息）"""
    return db.query(User).options(joinedload(User.roles)).filter(User.id == user_id).first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None
) -> tuple[List[User], int]:
    """获取用户列表（包含角色信息）"""
    from sqlalchemy.orm import joinedload
    
    query = db.query(User).options(joinedload(User.roles))
    
    # 按角色筛选（通过关联表）
    if role:
        query = query.join(User.roles).filter(Role.code == role)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return users, total


def update_user(
    db: Session,
    user_id: int,
    user_update: UserUpdate,
    current_user: User
) -> User:
    """更新用户信息"""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查：只能修改自己的信息，或管理员可以修改所有信息
    if user_id != current_user.id and not current_user.has_role(RoleType.SYSTEM_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此用户信息"
        )
    
    # 更新字段
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.status_tag is not None:
        user.status_tag = user_update.status_tag
    if user_update.is_active is not None:
        # 只有管理员可以修改is_active
        if not current_user.has_role(RoleType.SYSTEM_ADMIN.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以修改用户激活状态"
            )
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    return user


def add_user_role(
    db: Session,
    user_id: int,
    role_code: str,
    current_user: User
) -> User:
    """为用户添加角色（仅管理员）"""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查：只有管理员可以修改角色
    if not current_user.has_role(RoleType.SYSTEM_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改用户角色"
        )
    
    # 检查角色是否已存在
    if user.has_role(role_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户已拥有角色: {role_code}"
        )
    
    # 获取或创建角色
    role = RoleService.get_or_create_role_by_code(db, role_code)
    user.roles.append(role)
    
    db.commit()
    db.refresh(user)
    return user


def remove_user_role(
    db: Session,
    user_id: int,
    role_code: str,
    current_user: User
) -> User:
    """移除用户角色（仅管理员）"""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查：只有管理员可以修改角色
    if not current_user.has_role(RoleType.SYSTEM_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改用户角色"
        )
    
    # 不能移除自己的系统管理员角色
    if user_id == current_user.id and role_code == RoleType.SYSTEM_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除自己的系统管理员角色"
        )
    
    # 检查角色是否存在
    if not user.has_role(role_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"用户不拥有角色: {role_code}"
        )
    
    # 移除角色
    role = RoleService.get_role_by_code(db, role_code)
    if role:
        user.roles.remove(role)
    
    db.commit()
    db.refresh(user)
    return user


def set_user_roles(
    db: Session,
    user_id: int,
    role_codes: List[str],
    current_user: User
) -> User:
    """设置用户角色列表（替换所有角色，仅管理员）"""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查：只有管理员可以修改角色
    if not current_user.has_role(RoleType.SYSTEM_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改用户角色"
        )
    
    # 不能移除自己的系统管理员角色
    if user_id == current_user.id:
        if RoleType.SYSTEM_ADMIN.value not in role_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能移除自己的系统管理员角色"
            )
    
    # 清空现有角色
    user.roles.clear()
    
    # 添加新角色
    for role_code in role_codes:
        role = RoleService.get_or_create_role_by_code(db, role_code)
        user.roles.append(role)
    
    db.commit()
    db.refresh(user)
    return user


def update_user_role(
    db: Session,
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: User
) -> User:
    """更新用户角色（向后兼容，仅添加单个角色）"""
    return add_user_role(db, user_id, role_update.role.value, current_user)


def delete_user(
    db: Session,
    user_id: int,
    current_user: User
) -> bool:
    """删除用户（仅管理员）"""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查：只有管理员可以删除用户
    if not current_user.has_role(RoleType.SYSTEM_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以删除用户"
        )
    
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    db.delete(user)
    db.commit()
    return True


def create_user_by_admin(
    db: Session,
    user_data: UserCreate,
    current_user: User
) -> User:
    """管理员创建用户（使用默认密码）"""
    # 权限检查：只有管理员可以创建用户
    if not current_user.has_role(RoleType.SYSTEM_ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建用户"
        )
    
    # 确定角色
    role = UserRole.DEVELOPER
    if user_data.role_codes:
        # 如果指定了角色代码，使用第一个角色代码对应的UserRole
        # 这里简化处理，实际应该根据role_codes设置角色
        role = UserRole.DEVELOPER
    
    # 使用默认密码创建用户
    user = create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=settings.DEFAULT_USER_PASSWORD,
        full_name=user_data.full_name,
        role=role
    )
    
    # 设置激活状态
    user.is_active = user_data.is_active
    db.commit()
    db.refresh(user)
    
    # 如果指定了角色代码，设置角色
    if user_data.role_codes:
        user.roles.clear()
        for role_code in user_data.role_codes:
            role_obj = RoleService.get_or_create_role_by_code(db, role_code)
            user.roles.append(role_obj)
        db.commit()
        db.refresh(user)
    
    return user
