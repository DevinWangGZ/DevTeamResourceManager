"""认证相关端点"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.services.user_service import get_user
from app.schemas.auth import (
    Token,
    UserLogin,
    UserRegister,
    PasswordChange,
)
from app.schemas.user import UserResponse
from app.services.auth_service import (
    authenticate_user,
    create_user,
    generate_token_for_user,
    change_password,
)
from app.models.user import User, UserRole

router = APIRouter()


@router.post("/login", response_model=Token, summary="用户登录")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    
    返回访问令牌
    """
    # 支持用户名或邮箱登录
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        # 尝试使用邮箱登录
        user_by_email = db.query(User).filter(User.email == form_data.username).first()
        if user_by_email:
            user = authenticate_user(db, user_by_email.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = generate_token_for_user(user)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    用户注册
    
    - **username**: 用户名（唯一）
    - **email**: 邮箱（唯一）
    - **password**: 密码
    - **full_name**: 全名（可选）
    
    返回注册的用户信息
    """
    user = create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        role=UserRole.DEVELOPER  # 默认角色为开发人员
    )
    return user


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前登录用户的信息
    
    需要提供有效的访问令牌
    """
    # 确保加载角色信息
    user = get_user(db, current_user.id)
    return UserResponse.from_user(user) if user else UserResponse.from_user(current_user)


@router.post("/change-password", summary="修改密码")
async def change_password_endpoint(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改当前用户的密码
    
    - **old_password**: 原密码
    - **new_password**: 新密码（至少8个字符）
    
    需要提供有效的访问令牌和正确的原密码
    """
    # 验证新密码长度
    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码长度至少为8个字符"
        )
    
    user = change_password(
        db=db,
        user=current_user,
        old_password=password_data.old_password,
        new_password=password_data.new_password
    )
    return {"message": "密码修改成功"}
