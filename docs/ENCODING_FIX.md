# 字符编码问题修复说明

## 问题描述

系统页面出现中文乱码，显示为类似 `ä»»åŠ¡lï¼ç"¨æ^•ç™»å½•åŠŸèƒ½` 的乱码字符。

## 修复内容

### 1. 后端修复

#### 1.1 FastAPI响应编码
- 在所有 `JSONResponse` 中添加 `media_type="application/json; charset=utf-8"`
- 创建编码中间件确保所有响应使用UTF-8编码

#### 1.2 数据库连接编码
- MySQL连接字符串添加 `use_unicode=1` 参数
- 数据库连接参数添加 `use_unicode: True`

#### 1.3 修改的文件
- `backend/app/main.py` - 添加编码中间件和响应编码设置
- `backend/app/core/config.py` - 数据库URL添加use_unicode参数
- `backend/app/db/session.py` - 连接参数添加use_unicode
- `backend/app/middleware/encoding.py` - 新建编码中间件

### 2. 前端修复

#### 2.1 API请求编码
- Axios请求头添加 `charset=utf-8`
- 设置 `responseEncoding: 'utf8'`

#### 2.2 修改的文件
- `frontend/src/api/index.ts` - 更新请求配置

### 3. HTML编码（已正确）
- `frontend/index.html` 已设置 `<meta charset="UTF-8">`

## 验证步骤

1. **重启后端服务**
   ```bash
   # 停止当前后端服务（Ctrl+C）
   # 重新启动
   make dev-backend
   ```

2. **刷新前端页面**
   - 清除浏览器缓存（Ctrl+Shift+R 或 Cmd+Shift+R）
   - 刷新页面查看中文显示是否正常

3. **检查API响应**
   ```bash
   # 检查响应头
   curl -I http://localhost:8000/api/v1/tasks
   
   # 应该看到 Content-Type: application/json; charset=utf-8
   ```

4. **检查数据库编码**
   ```sql
   -- 检查数据库字符集
   SHOW VARIABLES LIKE 'character_set%';
   
   -- 检查表字符集
   SHOW CREATE TABLE tasks;
   ```

## 如果问题仍然存在

### 检查数据库字符集

确保数据库和表使用UTF-8编码：

```sql
-- 检查数据库字符集
SHOW CREATE DATABASE devteam_manager;

-- 如果数据库不是utf8mb4，需要修改
ALTER DATABASE devteam_manager CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 检查表字符集
SHOW CREATE TABLE tasks;

-- 如果表不是utf8mb4，需要修改
ALTER TABLE tasks CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 检查现有数据

如果数据库中已有乱码数据，可能需要：
1. 删除乱码数据
2. 重新插入正确编码的数据
3. 或者使用数据迁移工具修复编码

### 浏览器检查

1. 打开浏览器开发者工具（F12）
2. 查看Network标签
3. 检查API响应的Content-Type头
4. 检查响应内容的编码

## 预防措施

1. **数据库创建时指定字符集**
   ```sql
   CREATE DATABASE devteam_manager 
   CHARACTER SET utf8mb4 
   COLLATE utf8mb4_unicode_ci;
   ```

2. **表创建时指定字符集**
   ```sql
   CREATE TABLE tasks (
     ...
   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
   ```

3. **应用层面**
   - 确保所有API响应明确指定UTF-8编码
   - 确保前端请求和响应都使用UTF-8
   - 使用编码中间件统一处理

## 相关文档

- [MySQL字符集设置](https://dev.mysql.com/doc/refman/8.0/en/charset.html)
- [FastAPI响应编码](https://fastapi.tiangolo.com/advanced/custom-response/)
- [Axios编码配置](https://axios-http.com/docs/config_defaults)
