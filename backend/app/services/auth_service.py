"""认证服务"""
import logging
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

logger = logging.getLogger(__name__)

# 用于不存在用户时的密码校验，避免明显的时序差异
DUMMY_PASSWORD_HASH = "$2b$12$fhgjHmubsEcrcTJATjUztOwcBl3fFbqj32zgjQAoPw0gtjBLERTda"


def get_user_for_login_identifier(db: Session, identifier: str) -> Optional[User]:
    """按用户名或邮箱获取用户"""
    return db.query(User).filter((User.username == identifier) | (User.email == identifier)).first()


def check_login_lock(user: User) -> None:
    """检查登录锁定状态"""
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="登录失败次数过多，请稍后再试",
        )


def record_failed_login(db: Session, user: Optional[User]) -> None:
    """记录登录失败并在达到阈值时锁定账号"""
    if not user:
        return

    now = datetime.utcnow()
    window_start = now - timedelta(minutes=settings.LOGIN_FAILURE_WINDOW_MINUTES)

    if not user.last_failed_login_at or user.last_failed_login_at < window_start:
        user.failed_login_attempts = 0

    user.failed_login_attempts += 1
    user.last_failed_login_at = now

    if user.failed_login_attempts >= settings.LOGIN_MAX_FAILED_ATTEMPTS:
        user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
        logger.warning(
            "用户登录失败达到阈值并锁定: user_id=%s username=%s lock_until=%s",
            user.id,
            user.username,
            user.locked_until,
        )

    db.commit()


def clear_login_failures(db: Session, user: User) -> None:
    """登录成功后清理失败计数和锁定状态"""
    user.failed_login_attempts = 0
    user.last_failed_login_at = None
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    db.commit()


def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    """验证用户身份"""
    user = get_user_for_login_identifier(db, identifier)

    if not user:
        verify_password(password, DUMMY_PASSWORD_HASH)
        return None

    check_login_lock(user)

    if not verify_password(password, user.password_hash):
        record_failed_login(db, user)
        return None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )

    clear_login_failures(db, user)
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
