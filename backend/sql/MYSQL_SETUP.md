# MySQL 数据库配置说明

## 数据库信息

- **主机**: 10.254.68.77
- **端口**: 3306
- **数据库名**: devteam_manager
- **用户**: root
- **密码**: 123456
- **MySQL版本**: 5.7.35

## 配置更新

### 1. 依赖更新

已添加MySQL驱动依赖到 `requirements/base.txt`:
- `pymysql>=1.1.0` - MySQL Python驱动
- `cryptography>=3.4.0` - 加密支持（已存在）

### 2. 配置文件更新

#### `app/core/config.py`

新增配置项：
- `DATABASE_TYPE`: 数据库类型（mysql/postgresql/sqlite），默认 `mysql`
- `MYSQL_SERVER`: MySQL服务器地址
- `MYSQL_USER`: MySQL用户名
- `MYSQL_PASSWORD`: MySQL密码
- `MYSQL_DB`: MySQL数据库名
- `MYSQL_PORT`: MySQL端口

`database_url` 属性已更新，支持根据 `DATABASE_TYPE` 自动构建MySQL连接URL。

#### `app/db/session.py`

更新了数据库引擎配置：
- 添加MySQL连接参数（charset=utf8mb4）
- 启用连接池预检查（pool_pre_ping）
- 设置连接回收时间（pool_recycle=3600）

### 3. 环境变量配置

创建了 `env.example` 文件，包含所有配置项的示例。

要使用配置，请：
1. 复制 `env.example` 为 `.env`
2. 根据需要修改配置值

## 数据库连接测试

已成功测试数据库连接，可以正常：
- ✅ 连接到MySQL数据库
- ✅ 查询用户表数据
- ✅ 验证数据完整性

## 使用说明

### 方式1：使用环境变量（推荐）

创建 `.env` 文件：
```env
DATABASE_TYPE=mysql
MYSQL_SERVER=10.254.68.77
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DB=devteam_manager
MYSQL_PORT=3306
```

### 方式2：直接指定DATABASE_URL

```env
DATABASE_URL=mysql+pymysql://root:123456@10.254.68.77:3306/devteam_manager?charset=utf8mb4
```

### 方式3：使用默认配置

如果不设置环境变量，将使用代码中的默认值（已配置为MySQL）。

## 数据库表结构

已创建12个核心表：
1. users - 用户表
2. skills - 技能表
3. experiences - 业务履历表
4. projects - 项目表
5. tasks - 任务表
6. user_sequences - 序列管理表
7. task_schedules - 任务排期表
8. holidays - 节假日表
9. project_output_values - 项目产值统计表
10. workload_statistics - 工作量统计表
11. articles - 知识分享表
12. messages - 消息通知表

## 注意事项

1. **字符集**: 使用 `utf8mb4` 以支持完整的Unicode字符（包括emoji）
2. **存储引擎**: 所有表使用 `InnoDB` 引擎，支持事务和外键
3. **时区**: MySQL服务器时区设置会影响时间戳字段
4. **连接池**: 已配置连接池，避免频繁创建连接
5. **密码安全**: 生产环境请使用强密码，并考虑使用环境变量或密钥管理服务

## 切换数据库

如果需要切换到其他数据库类型：

### 切换到PostgreSQL
```env
DATABASE_TYPE=postgresql
POSTGRES_SERVER=localhost
POSTGRES_USER=devteam
POSTGRES_PASSWORD=devteam123
POSTGRES_DB=devteam_manager
POSTGRES_PORT=5432
```

### 切换到SQLite（开发环境）
```env
USE_SQLITE=True
SQLITE_DB=devteam_manager.db
```

## 故障排查

### 连接失败
1. 检查网络连接：`ping 10.254.68.77`
2. 检查MySQL服务是否运行
3. 检查防火墙设置
4. 验证用户名和密码

### 字符编码问题
确保连接URL中包含 `charset=utf8mb4`，数据库和表都使用 `utf8mb4` 字符集。

### 时区问题
如果遇到时区相关的问题，可以在连接URL中添加时区参数：
```
?charset=utf8mb4&time_zone=%2B08%3A00
```
