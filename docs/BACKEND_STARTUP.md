# 后端服务启动指南

## 正确的启动方式

### 方式一：使用 Makefile（推荐）

```bash
# 从项目根目录运行
make dev-backend
```

这会自动：
1. 切换到 `backend` 目录
2. 使用 `uvicorn` 启动服务
3. 启用热重载（--reload）

### 方式二：使用 uvicorn 命令

```bash
# 切换到backend目录
cd backend

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 方式三：使用 run.py 脚本（开发调试）

```bash
# 切换到backend目录
cd backend

# 运行启动脚本
python run.py
```

## 为什么不能直接运行 main.py？

如果直接运行 `python backend/app/main.py`，会出现以下错误：

```
ModuleNotFoundError: No module named 'app'
```

**原因**：
- Python的模块搜索路径（sys.path）不包括 `backend` 目录
- `main.py` 中的导入语句 `from app.core.config import settings` 需要 `app` 模块在Python路径中
- 直接运行文件时，Python无法找到 `app` 模块

**解决方法**：
- 使用 `uvicorn` 命令（推荐）：`uvicorn app.main:app`
- 使用 `run.py` 脚本：会自动添加路径
- 或者设置 `PYTHONPATH` 环境变量

## 环境变量设置

如果需要设置 `PYTHONPATH`：

```bash
# Linux/Mac
export PYTHONPATH=/path/to/DevTeamResourceManager/backend:$PYTHONPATH

# Windows
set PYTHONPATH=C:\path\to\DevTeamResourceManager\backend;%PYTHONPATH%
```

## 常见问题

### 1. 端口被占用

如果8000端口被占用，可以修改端口：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### 2. 模块导入错误

确保：
- 在 `backend` 目录下运行命令
- 或者使用 `make dev-backend` 命令
- 或者使用 `run.py` 脚本

### 3. 依赖未安装

```bash
cd backend
pip install -r requirements/dev.txt
```

## 验证服务运行

启动后，访问以下地址验证：

- **API文档**：http://localhost:8000/docs
- **健康检查**：http://localhost:8000/health
- **API根路径**：http://localhost:8000/
