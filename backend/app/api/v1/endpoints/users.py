"""用户管理端点"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user
from app.core.permissions import (
    get_current_admin,
    get_current_development_lead,
    check_user_permission,
)
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserRoleUpdate,
    UserRolesUpdate,
    UserListResponse,
)
from app.services.user_service import (
    get_user,
    get_users,
    update_user,
    update_user_role,
    add_user_role,
    remove_user_role,
    set_user_roles,
    delete_user,
)
from app.models.role import RoleType
from app.models.user import User

router = APIRouter()


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


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新当前用户的信息
    
    可以修改：姓名、状态标签
    不能修改：角色、激活状态（需要管理员权限）
    """
    return update_user(db, current_user.id, user_update, current_user)


@router.get("/", response_model=UserListResponse, summary="获取用户列表")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: str = Query(None, description="按角色筛选"),
    is_active: bool = Query(None, description="按激活状态筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户列表
    
    - 开发人员：只能查看自己的信息
    - 开发组长：可以查看所有开发人员
    - 项目经理：可以查看所有用户
    - 系统管理员：可以查看所有用户
    """
    # 开发人员只能查看自己的信息
    if current_user.has_role(RoleType.DEVELOPER.value) and not current_user.has_any_role([
        RoleType.PROJECT_MANAGER.value,
        RoleType.DEVELOPMENT_LEAD.value,
        RoleType.SYSTEM_ADMIN.value
    ]):
        users = [current_user]
        total = 1
    else:
        # 其他角色可以查看用户列表
        users, total = get_users(
            db,
            skip=skip,
            limit=limit,
            role=role,
            is_active=is_active
        )
    
    # 转换为UserResponse格式
    items = [UserResponse.from_user(user) for user in users]
    
    return {
        "total": total,
        "items": items
    }


@router.get("/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user_detail(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取指定用户的详细信息
    
    - 开发人员：只能查看自己的信息
    - 其他角色：可以查看所有用户信息
    """
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 权限检查
    if not check_user_permission(current_user, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限查看此用户信息"
        )
    
    return UserResponse.from_user(user)


@router.put("/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user_detail(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新用户信息
    
    - 用户可以更新自己的信息
    - 管理员可以更新所有用户信息
    """
    user = update_user(db, user_id, user_update, current_user)
    return UserResponse.from_user(user)


@router.put("/{user_id}/role", response_model=UserResponse, summary="更新用户角色（向后兼容，添加单个角色）")
async def update_user_role_endpoint(
    user_id: int,
    role_update: UserRoleUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    更新用户角色（向后兼容，仅添加单个角色）
    
    可以修改用户的角色，但不能修改自己的角色
    """
    user = update_user_role(db, user_id, role_update, current_user)
    return UserResponse.from_user(user)


@router.post("/{user_id}/roles", response_model=UserResponse, summary="添加用户角色")
async def add_user_role_endpoint(
    user_id: int,
    role_code: str = Query(..., description="角色代码"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    为用户添加角色（仅系统管理员）
    """
    user = add_user_role(db, user_id, role_code, current_user)
    return UserResponse.from_user(user)


@router.delete("/{user_id}/roles/{role_code}", response_model=UserResponse, summary="移除用户角色")
async def remove_user_role_endpoint(
    user_id: int,
    role_code: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    移除用户角色（仅系统管理员）
    """
    user = remove_user_role(db, user_id, role_code, current_user)
    return UserResponse.from_user(user)


@router.put("/{user_id}/roles", response_model=UserResponse, summary="设置用户角色列表")
async def set_user_roles_endpoint(
    user_id: int,
    roles_update: UserRolesUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    设置用户角色列表（替换所有角色，仅系统管理员）
    """
    user = set_user_roles(db, user_id, roles_update.role_codes, current_user)
    return UserResponse.from_user(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除用户")
async def delete_user_endpoint(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    删除用户（仅系统管理员）
    
    可以删除用户，但不能删除自己
    """
    delete_user(db, user_id, current_user)
    return None
