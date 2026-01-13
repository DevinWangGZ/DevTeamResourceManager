# SQL 脚本说明

本目录包含 DevTeam Manager 项目的数据库建表语句和初始化脚本。

## 文件说明

### 01_create_tables.sql
核心数据库表结构定义，包含以下表：

1. **users** - 用户表
   - 存储用户基本信息、角色、状态标签等

2. **skills** - 技能表
   - 存储用户的技能信息（技能名、熟练度）

3. **experiences** - 业务履历表
   - 存储用户的项目经历（项目、模块、角色、投入人天等）

4. **projects** - 项目表
   - 存储项目信息、预计产值等

5. **tasks** - 任务表
   - 存储任务信息、状态、投入人天等

6. **user_sequences** - 序列管理表
   - 存储用户的序列等级和单价（用于产值计算）

7. **task_schedules** - 任务排期表
   - 存储任务的排期信息（开始日期、结束日期、是否置顶）

8. **holidays** - 节假日表
   - 存储节假日信息，用于排期计算时排除

9. **project_output_values** - 项目产值统计表
   - 存储项目的产值统计信息

10. **workload_statistics** - 工作量统计表
    - 存储用户的工作量统计信息

11. **articles** - 知识分享表（后续功能）
    - 存储知识分享文章（Markdown格式）

12. **messages** - 消息通知表（后续功能）
    - 存储系统消息和通知

## 执行顺序

1. 先执行 `01_create_tables.sql` 创建所有表结构
2. 再执行 `02_init_data.sql` 插入初始测试数据（可选）

## 使用说明

### MySQL（当前使用）

```bash
# 连接到MySQL数据库
mysql -h 10.254.68.77 -u root -p123456

# 执行建表语句
mysql -h 10.254.68.77 -u root -p123456 < backend/sql/01_create_tables_mysql.sql

# 执行初始化数据（可选）
mysql -h 10.254.68.77 -u root -p123456 < backend/sql/02_init_data_mysql.sql
```

### PostgreSQL（备用）

```bash
# 连接到数据库
psql -U devteam -d devteam_manager

# 执行建表语句
\i backend/sql/01_create_tables.sql

# 执行初始化数据（可选）
\i backend/sql/02_init_data.sql
```

### SQLite（开发环境）

```bash
# 使用 sqlite3 命令行工具
sqlite3 devteam_manager.db < backend/sql/01_create_tables.sql
sqlite3 devteam_manager.db < backend/sql/02_init_data.sql
```

## 注意事项

1. **密码哈希**：`02_init_data.sql` 中的密码哈希值仅为示例，实际部署时需要替换为应用生成的正确哈希值。

2. **外键约束**：所有表都设置了外键约束，确保数据完整性。

3. **索引**：已为常用查询字段创建索引，提升查询性能。

4. **触发器**：已为需要自动更新 `updated_at` 字段的表创建触发器。

5. **字符集**：建议使用 UTF-8 字符集，支持中文和特殊字符。

## 数据模型关系

```
users (1) ──< (N) skills
users (1) ──< (N) experiences
users (1) ──< (N) user_sequences
users (1) ──< (N) tasks (creator_id)
users (1) ──< (N) tasks (assignee_id)
projects (1) ──< (N) tasks
tasks (1) ──< (1) task_schedules
projects (1) ──< (1) project_output_values
users (1) ──< (N) workload_statistics
projects (1) ──< (N) workload_statistics
```

## 后续扩展

- 如需添加新表，请在 `01_create_tables.sql` 文件末尾添加
- 如需修改表结构，建议创建新的迁移脚本
- 初始化数据脚本可根据实际需求调整
