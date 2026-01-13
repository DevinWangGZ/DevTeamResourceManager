# MySQL字符集乱码问题修复指南

## 问题描述

数据库表字段注释和数据显示乱码，如：`ä»»åŠ¡lï¼ç"¨æ^•ç™»å½•åŠŸèƒ½`

## 根本原因

1. **SQL文件编码问题**：SQL文件可能不是UTF-8编码
2. **MySQL客户端连接字符集**：客户端连接时未设置UTF-8字符集
3. **数据库/表字符集**：数据库或表未使用utf8mb4字符集
4. **数据插入时字符集**：插入数据时连接字符集不正确

## 修复步骤

### 第一步：检查当前状态

```sql
-- 检查数据库字符集
SHOW CREATE DATABASE devteam_manager;

-- 检查表字符集
SHOW CREATE TABLE users;
SHOW CREATE TABLE tasks;

-- 检查当前连接字符集
SHOW VARIABLES LIKE 'character_set%';
```

### 第二步：修复数据库和表字符集

```sql
-- 1. 修改数据库字符集
ALTER DATABASE devteam_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 修改所有表的字符集
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE skills CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE experiences CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE projects CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE tasks CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE user_sequences CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE task_schedules CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE holidays CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE project_output_values CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE workload_statistics CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE articles CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE messages CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 第三步：重新执行SQL脚本（推荐方式）

**方式1：使用脚本（推荐）**

```bash
# 使用提供的初始化脚本
./scripts/init_mysql_db.sh
```

**方式2：手动执行**

```bash
# 1. 删除现有数据库（谨慎操作！）
mysql -h 10.254.68.77 -u root -p123456 -e "DROP DATABASE IF EXISTS devteam_manager;"

# 2. 使用UTF-8字符集重新创建
mysql -h 10.254.68.77 -u root -p123456 --default-character-set=utf8mb4 < backend/sql/01_create_tables_mysql.sql

# 3. 使用UTF-8字符集插入数据
mysql -h 10.254.68.77 -u root -p123456 --default-character-set=utf8mb4 < backend/sql/02_init_data_mysql.sql
```

**方式3：在MySQL客户端中执行**

```bash
# 连接MySQL（设置字符集）
mysql -h 10.254.68.77 -u root -p123456 --default-character-set=utf8mb4

# 在MySQL客户端中执行
SET NAMES utf8mb4;
source backend/sql/00_setup_charset.sql;
source backend/sql/01_create_tables_mysql.sql;
source backend/sql/02_init_data_mysql.sql;
```

### 第四步：验证修复结果

```sql
-- 1. 检查数据库字符集
SHOW CREATE DATABASE devteam_manager;
-- 应该看到: DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci

-- 2. 检查表字符集
SHOW CREATE TABLE users;
-- 应该看到: ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- 3. 检查字段注释
SHOW FULL COLUMNS FROM users;
-- 注释应该正常显示中文

-- 4. 检查数据
SELECT * FROM users LIMIT 5;
-- 数据应该正常显示中文
```

## 预防措施

### 1. SQL文件编码

确保所有SQL文件使用UTF-8编码保存：
- 在编辑器中设置文件编码为UTF-8
- 不要使用Windows记事本编辑（可能使用GBK编码）

### 2. MySQL客户端连接

**推荐方式**：
```bash
mysql -h 10.254.68.77 -u root -p123456 --default-character-set=utf8mb4
```

**或在连接后设置**：
```sql
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4;
```

### 3. 执行SQL脚本

**推荐方式**：
```bash
mysql -h 10.254.68.77 -u root -p123456 --default-character-set=utf8mb4 < script.sql
```

### 4. 应用连接

确保应用连接数据库时使用UTF-8字符集：
- 连接字符串包含 `charset=utf8mb4`
- 连接参数设置 `use_unicode=True`

## 已修复的SQL文件

以下SQL文件已更新，包含字符集设置：

1. `backend/sql/00_setup_charset.sql` - 字符集设置脚本（新建）
2. `backend/sql/01_create_tables_mysql.sql` - 建表语句（已添加字符集设置）
3. `backend/sql/02_init_data_mysql.sql` - 初始化数据（已添加字符集设置）

## 快速修复脚本

已创建自动化脚本：
- `scripts/init_mysql_db.sh` - 自动初始化数据库（包含字符集设置）

使用方法：
```bash
chmod +x scripts/init_mysql_db.sh
./scripts/init_mysql_db.sh
```

## 常见问题

### Q1: 修改字符集后，现有数据还是乱码？

**A**: 需要重新插入数据。字符集修改只影响新数据，不会自动转换现有数据。

### Q2: 如何检查SQL文件编码？

**A**: 
```bash
# Linux/Mac
file -I script.sql

# 应该显示: text/plain; charset=utf-8
```

### Q3: 使用Navicat等GUI工具如何设置？

**A**: 
- 在连接设置中，字符集选择 `utf8mb4`
- 或在查询前执行：`SET NAMES utf8mb4;`

### Q4: 如何批量修改所有表的字符集？

**A**: 
```sql
-- 生成修改语句
SELECT CONCAT('ALTER TABLE ', table_name, ' CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;')
FROM information_schema.tables
WHERE table_schema = 'devteam_manager'
AND table_type = 'BASE TABLE';

-- 复制生成的SQL并执行
```

## 相关文档

- [MySQL字符集文档](https://dev.mysql.com/doc/refman/8.0/en/charset.html)
- [utf8mb4字符集说明](https://dev.mysql.com/doc/refman/8.0/en/charset-unicode-utf8mb4.html)
