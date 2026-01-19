"""认证服务"""
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户身份"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return user


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    full_name: Optional[str] = None,
    role: Optional[UserRole] = None
) -> User:
    """创建新用户"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建用户
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        password_hash=hashed_password,
        full_name=full_name,
        role=role or UserRole.DEVELOPER
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户（包含角色信息）"""
    from sqlalchemy.orm import joinedload
    return db.query(User).options(joinedload(User.roles)).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def generate_token_for_user(user: User) -> str:
    """为用户生成访问令牌"""
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
        expires_delta=access_token_expires
    )


def change_password(
    db: Session,
    user: User,
    old_password: str,
    new_password: str
) -> User:
    """修改用户密码"""
    # 验证旧密码
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )
    
    # 更新密码
    user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user
