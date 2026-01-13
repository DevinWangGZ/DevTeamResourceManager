# 快速启动指南

> 本文档帮助您快速搭建开发环境并启动项目

## 前置要求

- Python 3.12+ (当前使用 3.13.9)
- Node.js 18.0+
- Docker & Docker Compose (可选，用于PostgreSQL)

## 快速开始

### 1. 后端设置

```bash
# 进入后端目录
cd backend

# 安装依赖（使用conda环境中的Python）
/opt/miniconda3/bin/pip install -r requirements/dev.txt

# 或激活conda环境后安装
conda activate base
pip install -r requirements/dev.txt

# 复制环境变量文件
cp .env.example .env

# 编辑.env文件，配置数据库等信息
# 开发环境建议使用SQLite：设置 USE_SQLITE=True
```

### 2. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 复制环境变量文件
cp .env.example .env.development

# 编辑.env.development文件，配置API地址
```

### 3. 启动服务

#### 方式1：使用Makefile（推荐）

```bash
# 安装所有依赖
make install

# 启动后端（新终端）
make dev-backend

# 启动前端（新终端）
make dev-frontend
```

#### 方式2：手动启动

**后端：**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**
```bash
cd frontend
npm run dev
```

### 4. 访问应用

- **前端**：http://localhost:5173
- **后端API**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

## 数据库设置

### 使用SQLite（开发环境，推荐）

在 `backend/.env` 中设置：
```env
USE_SQLITE=True
SQLITE_DB=devteam_manager.db
```

### 使用PostgreSQL

1. 启动PostgreSQL容器：
```bash
docker-compose up -d postgres
```

2. 在 `backend/.env` 中配置：
```env
USE_SQLITE=False
POSTGRES_SERVER=localhost
POSTGRES_USER=devteam
POSTGRES_PASSWORD=devteam123
POSTGRES_DB=devteam_manager
```

3. 运行数据库迁移：
```bash
cd backend
alembic revision --autogenerate -m "初始化数据库"
alembic upgrade head
```

## 下一步

完成基础搭建后，继续实现：
1. 用户模型和认证系统
2. 数据库迁移
3. 基础API端点

详细开发计划请参考：[实施路线图](./docs/IMPLEMENTATION_ROADMAP.md)
