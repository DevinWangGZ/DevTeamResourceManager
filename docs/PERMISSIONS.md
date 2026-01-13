# 权限管理说明

> **文档版本**：v1.0 | **更新日期**：2024-05 | **负责人**：项目组

## 概述

DevTeam Manager 采用基于角色的访问控制（RBAC）机制，通过用户角色来管理权限。

## 用户角色

系统定义了4种用户角色：

1. **开发人员 (developer)**
   - 基础角色，所有注册用户默认角色
   - 可以维护自己的档案、认领任务、提交任务

2. **项目经理 (project_manager)**
   - 可以发布任务、确认任务、管理项目产值
   - 可以查看项目进展数据

3. **开发组长 (development_lead)**
   - 可以查看整个开发团队的仪表盘
   - 可以查阅每个人的工作负荷
   - 可以查看团队数据

4. **系统管理员 (system_admin)**
   - 最高权限，可以管理所有用户
   - 可以修改用户角色、激活状态
   - 可以删除用户

## 权限层级

权限采用层级设计，高级角色自动拥有低级角色的权限：

```
系统管理员 (最高权限)
    ↓
开发组长
    ↓
项目经理
    ↓
开发人员 (基础权限)
```

## 权限依赖函数

### 基础依赖

- `get_current_user` - 获取当前登录用户（所有认证用户）

### 角色权限依赖

- `get_current_developer` - 开发人员及以上（所有用户）
- `get_current_project_manager` - 项目经理及以上
- `get_current_development_lead` - 开发组长及以上
- `get_current_admin` - 仅系统管理员

### 使用示例

```python
from app.core.permissions import get_current_admin, get_current_project_manager

@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    current_user: User = Depends(get_current_admin),  # 仅管理员
    db: Session = Depends(get_db)
):
    # 只有管理员可以执行
    ...
```

## 权限检查函数

### check_user_permission

检查用户是否有权限访问资源：

```python
from app.core.permissions import check_user_permission

# 检查用户是否可以访问某个资源
if not check_user_permission(current_user, resource_user_id):
    raise HTTPException(status_code=403, detail="无权限")
```

**权限规则**：
- 系统管理员可以访问所有资源
- 用户可以访问自己的资源
- 开发组长可以访问开发人员的资源

## API权限说明

### 用户管理API (`/api/v1/users`)

| 端点 | 方法 | 权限要求 | 说明 |
|------|------|----------|------|
| `/me` | GET | 所有用户 | 获取当前用户信息 |
| `/me` | PUT | 所有用户 | 更新当前用户信息 |
| `/` | GET | 所有用户 | 获取用户列表（开发人员只能看到自己） |
| `/{user_id}` | GET | 开发人员只能看自己，其他角色可看所有 | 获取用户详情 |
| `/{user_id}` | PUT | 自己或管理员 | 更新用户信息 |
| `/{user_id}/role` | PUT | 仅管理员 | 更新用户角色 |
| `/{user_id}` | DELETE | 仅管理员 | 删除用户 |

### 认证API (`/api/v1/auth`)

| 端点 | 方法 | 权限要求 | 说明 |
|------|------|----------|------|
| `/login` | POST | 公开 | 用户登录 |
| `/register` | POST | 公开 | 用户注册 |
| `/me` | GET | 所有用户 | 获取当前用户信息 |

## 权限控制实现

### 1. 依赖注入方式（推荐）

在API端点中使用依赖注入：

```python
from app.core.permissions import get_current_admin

@router.put("/{user_id}/role")
async def update_role(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # 只有管理员可以执行
    ...
```

### 2. 函数内检查

在函数内部进行权限检查：

```python
from app.core.permissions import check_user_permission

@router.get("/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_user_permission(current_user, user_id):
        raise HTTPException(status_code=403, detail="无权限")
    ...
```

## 测试账号

| 用户名 | 密码 | 角色 | 权限说明 |
|--------|------|------|----------|
| admin | password123 | 系统管理员 | 所有权限 |
| pm001 | password123 | 项目经理 | 项目管理权限 |
| lead001 | password123 | 开发组长 | 团队管理权限 |
| dev001 | password123 | 开发人员 | 基础权限 |

## 注意事项

1. **角色修改**：只有系统管理员可以修改用户角色
2. **自己保护**：不能修改或删除自己的角色
3. **数据隔离**：开发人员只能查看和修改自己的数据
4. **权限继承**：高级角色自动拥有低级角色的权限

## 扩展说明

如需添加新的权限检查，可以在 `app/core/permissions.py` 中添加新的依赖函数：

```python
def get_custom_permission(
    current_user: User = Depends(get_current_user)
) -> User:
    """自定义权限检查"""
    # 权限检查逻辑
    if not has_permission(current_user):
        raise HTTPException(status_code=403, detail="无权限")
    return current_user
```

---

**文档维护**：本文档随权限系统发展持续更新。
