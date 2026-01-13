# 测试账号信息

## 默认测试账号

根据初始化数据脚本（`backend/sql/02_init_data_mysql.sql`），系统预置了以下测试账号：

### 账号列表

| 用户名 | 邮箱 | 角色 | 密码 |
|--------|------|------|------|
| admin | admin@devteam.com | 系统管理员 | password123 |
| pm001 | pm001@devteam.com | 项目经理 | password123 |
| lead001 | lead001@devteam.com | 开发组长 | password123 |
| dev001 | dev001@devteam.com | 开发人员 | password123 |
| dev002 | dev002@devteam.com | 开发人员 | password123 |
| dev003 | dev003@devteam.com | 开发人员 | password123 |

### 默认密码

**所有测试账号的默认密码都是：`password123`**

### 重要提示

⚠️ **注意**：初始化数据脚本中的密码哈希值可能不是正确的 `password123` 的哈希值。

如果使用默认密码无法登录，请：

1. **方式一：使用注册功能创建新账号**
   - 访问登录页面
   - 点击"还没有账号？立即注册"
   - 创建新账号并设置密码

2. **方式二：重新生成密码哈希并更新数据库**
   ```bash
   # 生成密码哈希
   cd backend
   python ../scripts/generate_password_hash.py password123
   
   # 更新数据库中的密码哈希
   mysql -h 10.254.68.77 -u root -p123456 devteam_manager -e "
   UPDATE users SET password_hash = '生成的哈希值' WHERE username = 'admin';
   "
   ```

3. **方式三：使用应用重置密码功能**（如果已实现）

### 生成正确的密码哈希

如果需要生成正确的密码哈希值，可以使用提供的脚本：

```bash
# 生成密码哈希
python scripts/generate_password_hash.py password123

# 输出示例：
# 密码: password123
# 哈希值: $2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 更新数据库密码

如果需要更新数据库中的密码哈希：

```sql
-- 更新单个用户密码
UPDATE users 
SET password_hash = '生成的哈希值' 
WHERE username = 'admin';

-- 更新所有用户密码为 password123
-- 注意：需要先生成正确的哈希值
UPDATE users 
SET password_hash = '生成的哈希值';
```

### 测试建议

1. **开发环境**：使用测试账号登录
2. **生产环境**：必须修改所有默认密码
3. **安全建议**：定期更换密码，使用强密码策略

---

**文档维护**：本文档随测试账号变更持续更新。
