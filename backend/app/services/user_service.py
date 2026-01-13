"""用户服务"""
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.schemas.user import UserUpdate, UserRoleUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    is_active: Optional[bool] = None
) -> tuple[List[User], int]:
    """获取用户列表"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
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
    current_user_role = UserRole(current_user.role)
    if user_id != current_user.id and current_user_role != UserRole.SYSTEM_ADMIN:
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
        if current_user_role != UserRole.SYSTEM_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以修改用户激活状态"
            )
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    return user


def update_user_role(
    db: Session,
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: User
) -> User:
    """更新用户角色（仅管理员）"""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查：只有管理员可以修改角色
    current_user_role = UserRole(current_user.role)
    if current_user_role != UserRole.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以修改用户角色"
        )
    
    # 不能修改自己的角色
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )
    
    # 更新角色
    user.role = role_update.role.value
    
    db.commit()
    db.refresh(user)
    return user


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
    current_user_role = UserRole(current_user.role)
    if current_user_role != UserRole.SYSTEM_ADMIN:
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
