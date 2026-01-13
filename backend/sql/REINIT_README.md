# 数据库重新初始化说明

## 概述

`04_reinit_database.sql` 是一个完整的数据库重新初始化脚本，它会：
1. 删除现有数据库（如果存在）
2. 重新创建数据库
3. 创建所有表结构（包括角色表）
4. 初始化默认角色
5. 插入测试数据
6. 迁移用户角色关系

## 执行方式

### 方式1：使用 MySQL 命令行（推荐）

```bash
# 进入项目目录
cd /Users/wangwenhao/Documents/work/code.nosync/DevTeamResourceManager/backend

# 执行SQL脚本
mysql -u root -p < sql/04_reinit_database.sql
```

### 方式2：使用 MySQL Workbench 或其他客户端

1. 打开 MySQL Workbench 或其他 MySQL 客户端
2. 连接到 MySQL 服务器
3. 打开 `backend/sql/04_reinit_database.sql` 文件
4. 执行整个脚本

### 方式3：分步执行（如果遇到问题）

如果一次性执行失败，可以按顺序执行以下脚本：

```bash
# 1. 删除并创建数据库
mysql -u root -p < sql/00_setup_charset.sql

# 2. 创建基础表
mysql -u root -p < sql/01_create_tables_mysql.sql

# 3. 创建角色表
mysql -u root -p < sql/03_add_roles_tables.sql

# 4. 初始化数据
mysql -u root -p < sql/02_init_data_mysql.sql
```

## 注意事项

1. **数据备份**：执行此脚本会删除现有数据库，请确保已备份重要数据
2. **权限要求**：需要 MySQL root 权限或具有创建/删除数据库的权限
3. **字符集**：脚本会自动设置 UTF-8 字符集（utf8mb4）
4. **测试数据**：脚本会插入测试用户和数据，所有测试用户密码均为 `password123`

## 测试账户

执行完成后，可以使用以下测试账户登录：

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| admin | password123 | 系统管理员 | 拥有所有权限 |
| pm001 | password123 | 项目经理 | 可以管理项目和任务 |
| lead001 | password123 | 开发组长 | 可以查看团队数据 |
| dev001 | password123 | 开发人员 | 普通开发人员 |
| dev002 | password123 | 开发人员 | 普通开发人员 |
| dev003 | password123 | 开发人员 | 普通开发人员 |

## 验证

执行完成后，可以运行以下 SQL 验证：

```sql
USE devteam_manager;

-- 检查表是否创建成功
SHOW TABLES;

-- 检查角色是否初始化
SELECT * FROM roles;

-- 检查用户角色关系是否迁移成功
SELECT u.username, u.role, r.name, r.code
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
ORDER BY u.id;

-- 检查测试数据
SELECT COUNT(*) as user_count FROM users;
SELECT COUNT(*) as project_count FROM projects;
SELECT COUNT(*) as task_count FROM tasks;
```

## 故障排除

### 问题1：权限不足
```
ERROR 1044 (42000): Access denied for user
```
**解决方案**：使用 root 用户或具有足够权限的用户

### 问题2：数据库已存在
```
ERROR 1007 (HY000): Can't create database 'devteam_manager'; database exists
```
**解决方案**：脚本会自动删除现有数据库，如果仍有问题，手动删除：
```sql
DROP DATABASE IF EXISTS devteam_manager;
```

### 问题3：外键约束错误
```
ERROR 1215 (HY000): Cannot add foreign key constraint
```
**解决方案**：确保按顺序执行脚本，先创建被引用的表

## 多角色支持

执行完成后，系统已支持多角色管理：
- 一个用户可以拥有多个角色
- 角色通过 `user_roles` 关联表管理
- 原有的 `users.role` 字段保留用于向后兼容，但不再使用

可以通过以下 API 管理用户角色：
- `POST /api/v1/users/{user_id}/roles?role_code=project_manager` - 添加角色
- `DELETE /api/v1/users/{user_id}/roles/{role_code}` - 移除角色
- `PUT /api/v1/users/{user_id}/roles` - 设置角色列表
