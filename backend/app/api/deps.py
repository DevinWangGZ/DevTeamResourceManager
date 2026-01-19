"""依赖注入"""
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import settings
from app.core.security import verify_token
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """获取当前用户依赖"""
    from sqlalchemy.orm import joinedload
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id_int = int(user_id)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception
    
    # 使用 joinedload 加载 roles 关系
    from app.models.user import User
    user = db.query(User).options(joinedload(User.roles)).filter(User.id == user_id_int).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user


async def get_current_user_optional(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer)
) -> Optional[User]:
    """获取当前用户依赖（可选，用于允许未登录访问的端点）"""
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        user_id_int = int(user_id)
    except (JWTError, ValueError, TypeError):
        return None
    
    user = get_user_by_id(db, user_id_int)
    if user is None or not user.is_active:
        return None
    
    return user
