# DevTeam Manager Backend

后端API服务，基于FastAPI开发。

## 技术栈

- Python 3.12+
- FastAPI 0.104+
- SQLAlchemy 2.0+
- Alembic 1.13+
- PostgreSQL 15+ / SQLite（开发）

## 快速开始

### 1. 安装依赖

```bash
# 激活conda环境（如果使用）
conda activate base  # 或你的Python 3.12+环境

# 安装依赖
pip install -r requirements/dev.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，配置数据库等信息
```

### 3. 初始化数据库

```bash
# 使用SQLite（开发环境）
# 在.env中设置 USE_SQLITE=True

# 或使用PostgreSQL（需要先启动docker-compose）
docker-compose up -d postgres

# 运行数据库迁移
alembic revision --autogenerate -m "初始化数据库"
alembic upgrade head
```

### 4. 运行开发服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发命令

```bash
# 运行测试
pytest

# 代码格式化
black .

# 导入排序
isort .

# 类型检查
mypy app
```

## 项目结构

```
backend/
├── app/              # 应用代码
├── alembic/          # 数据库迁移
├── tests/            # 测试代码
└── requirements/     # 依赖管理
```
