# 前后端联调环境说明

> **文档版本**：v1.0 | **更新日期**：2024-05 | **负责人**：项目组

## 什么是前后端联调环境？

前后端联调环境是指确保前端和后端能够正常通信、协作开发的配置和工具集合。主要包括：

1. **环境变量配置** - 统一管理API地址、端口等配置
2. **CORS配置** - 允许前端跨域访问后端API
3. **API代理配置** - 前端开发服务器代理后端API请求
4. **错误处理统一** - 前后端统一的错误处理和提示
5. **开发工具配置** - 热重载、调试工具等
6. **启动脚本优化** - 简化开发启动流程

## 当前配置状态

### ✅ 已完成的配置

1. **CORS配置** (`backend/app/main.py`)
   - 已配置CORS中间件
   - 允许前端域名访问
   - 支持凭证传递

2. **API代理配置** (`frontend/vite.config.ts`)
   - 已配置Vite代理
   - `/api` 请求自动转发到后端

3. **API客户端配置** (`frontend/src/api/index.ts`)
   - 已配置Axios实例
   - 自动添加Token
   - 统一错误处理

4. **开发脚本** (`Makefile`)
   - 已提供启动命令
   - 已提供安装命令

### ⚠️ 需要完善的配置

1. **环境变量文件**
   - 创建前端 `.env.development` 示例文件
   - 创建后端 `.env` 示例文件（已有env.example）
   - 确保环境变量正确配置

2. **错误处理增强**
   - 统一错误响应格式
   - 前端错误提示优化
   - 网络错误处理

3. **开发工具配置**
   - 热重载配置检查
   - 调试工具配置
   - 日志配置

4. **启动流程优化**
   - 一键启动前后端
   - 健康检查脚本
   - 开发环境验证

## 配置说明

### 后端配置

**环境变量文件** (`backend/.env`):
```env
# 数据库配置
DATABASE_TYPE=mysql
MYSQL_SERVER=10.254.68.77
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DB=devteam_manager
MYSQL_PORT=3306

# JWT配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# CORS配置
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### 前端配置

**环境变量文件** (`frontend/.env.development`):
```env
# API基础地址
VITE_API_BASE_URL=http://localhost:8000

# 应用配置
VITE_APP_TITLE=DevTeam Manager (开发环境)
```

### API代理配置

前端开发服务器（Vite）会自动将 `/api` 开头的请求代理到后端：

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

这意味着：
- 前端请求：`/api/v1/auth/login`
- 实际请求：`http://localhost:8000/api/v1/auth/login`

## 开发流程

### 1. 启动后端

```bash
# 方式1：使用Makefile
make dev-backend

# 方式2：手动启动
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务地址：http://localhost:8000
API文档地址：http://localhost:8000/docs

### 2. 启动前端

```bash
# 方式1：使用Makefile
make dev-frontend

# 方式2：手动启动
cd frontend
npm run dev
```

前端服务地址：http://localhost:5173

### 3. 验证联调

1. 打开浏览器访问：http://localhost:5173
2. 打开开发者工具（F12）查看Network请求
3. 测试登录功能，确认API请求正常
4. 检查后端日志，确认请求到达

## 常见问题

### 1. CORS错误

**问题**：前端请求后端时出现CORS错误

**解决**：
- 检查 `backend/app/core/config.py` 中的 `BACKEND_CORS_ORIGINS` 配置
- 确保前端地址在允许列表中
- 重启后端服务

### 2. API请求404

**问题**：前端请求API返回404

**解决**：
- 检查后端服务是否启动
- 检查API路径是否正确
- 检查Vite代理配置

### 3. Token无效

**问题**：登录后Token无效

**解决**：
- 检查Token是否正确存储到localStorage
- 检查请求头是否正确添加Authorization
- 检查后端JWT配置

### 4. 环境变量不生效

**问题**：修改环境变量后不生效

**解决**：
- 前端：重启开发服务器（Vite需要重启）
- 后端：重启服务（或使用--reload自动重载）
- 检查环境变量文件路径和格式

## 下一步优化

1. **统一错误响应格式**
   - 后端统一错误码和错误格式
   - 前端统一错误处理和提示

2. **开发工具增强**
   - 添加API Mock功能（可选）
   - 添加请求日志记录
   - 添加性能监控

3. **自动化脚本**
   - 一键启动前后端
   - 健康检查脚本
   - 环境验证脚本

---

**文档维护**：本文档随开发环境变化持续更新。
