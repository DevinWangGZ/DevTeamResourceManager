# 后端技术栈与开发规范

> **文档版本**：v1.0 | **更新日期**：2024-05 | **负责人**：后端组

## 目录
- [核心框架](#核心框架)
- [数据库与缓存](#数据库与缓存)
- [项目结构](#项目结构)
- [代码规范](#代码规范)
- [测试规范](#测试规范)
- [部署配置](#部署配置)
- [开发流程](#开发流程)

---

## 核心框架

### Web框架
- **Python 3.12**：主开发语言
- **FastAPI 0.104+**：异步Web框架
- **Uvicorn 0.24+**：ASGI服务器
- **Pydantic 2.5+**：数据验证与设置管理

### ORM与数据库
- **SQLAlchemy 2.0+**：ORM框架
- **Alembic 1.13+**：数据库迁移工具
- **asyncpg 0.29+**：异步PostgreSQL驱动

### 安全与认证
- **Python-Jose 3.3+**：JWT令牌处理
- **Passlib 1.7+**：密码哈希
- **Bcrypt**：密码加密（通过Passlib）

### 其他工具
- **Pytest 7.4+**：测试框架
- **Black 23.12+**：代码格式化
- **isort 5.13+**：导入排序
- **mypy 1.7+**：类型检查（可选）

---

## 数据库与缓存

### 数据库
- **PostgreSQL 15+**：主数据库（生产环境）
- **SQLite 3.41+**：开发与测试数据库

### 缓存（可选）
- **Redis 7.2+**：缓存与会话存储
- **aioredis 2.0+**：异步Redis客户端

### 数据库选择策略
- **开发环境**：使用SQLite，快速启动
- **测试环境**：使用SQLite或PostgreSQL（根据测试需求）
- **生产环境**：必须使用PostgreSQL

---

## 项目结构

```
backend/
├── app/
│   ├── api/                    # API路由
│   │   ├── v1/                 # API v1版本
│   │   │   ├── endpoints/      # 端点模块
│   │   │   │   ├── auth.py    # 认证相关
│   │   │   │   ├── users.py   # 用户管理
│   │   │   │   ├── tasks.py   # 任务管理
│   │   │   │   ├── profiles.py # 人员档案
│   │   │   │   └── ...        # 其他端点
│   │   │   └── __init__.py
│   │   ├── deps.py            # 依赖注入
│   │   └── router.py          # 路由聚合
│   ├── core/                   # 核心配置
│   │   ├── config.py          # 配置管理
│   │   ├── security.py        # 安全相关
│   │   └── exceptions.py      # 异常处理
│   ├── models/                 # SQLAlchemy模型
│   │   ├── base.py            # 基础模型
│   │   ├── user.py            # 用户模型
│   │   ├── task.py            # 任务模型
│   │   └── ...                # 其他模型
│   ├── schemas/                # Pydantic模式
│   │   ├── request/           # 请求模式
│   │   ├── response/          # 响应模式
│   │   └── common.py          # 通用模式
│   ├── services/               # 业务逻辑服务
│   │   ├── auth_service.py    # 认证服务
│   │   ├── task_service.py    # 任务服务
│   │   └── ...                # 其他服务
│   ├── crud/                   # 数据库操作（可选模式）
│   ├── utils/                  # 工具函数
│   ├── worker/                 # 后台任务（可选）
│   └── main.py                 # 应用入口
├── alembic/                    # 数据库迁移
│   ├── versions/              # 迁移版本
│   └── env.py                 # 迁移环境
├── tests/                      # 测试目录
│   ├── conftest.py            # 测试配置
│   ├── test_api/              # API测试
│   ├── test_services/         # 服务测试
│   └── test_models/            # 模型测试
├── scripts/                    # 脚本目录
├── requirements/               # 依赖管理
│   ├── base.txt              # 基础依赖
│   ├── dev.txt               # 开发依赖
│   └── prod.txt              # 生产依赖
├── .env.example               # 环境变量示例
├── .env                       # 环境变量（本地，不提交）
├── alembic.ini                # Alembic配置
└── main.py                    # 应用入口（可选，与app/main.py二选一）
```

### 目录说明

- **app/api/**：API路由层，按版本划分
- **app/core/**：核心配置，包括安全、异常处理
- **app/models/**：数据库模型，使用SQLAlchemy ORM
- **app/schemas/**：Pydantic模式，用于请求/响应验证
- **app/services/**：业务逻辑层，处理核心业务
- **app/crud/**：数据库CRUD操作（可选，可直接在service中实现）
- **app/utils/**：工具函数库
- **alembic/**：数据库迁移脚本
- **tests/**：测试文件，结构与app目录对应

---

## 代码规范

### API端点设计

#### 端点结构
- 使用FastAPI的`APIRouter`组织路由
- 按业务模块划分端点文件
- 统一使用`response_model`定义响应模式
- 使用依赖注入管理数据库会话和用户认证

#### 端点示例

```python
# app/api/v1/endpoints/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user, get_current_manager
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import task_service
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务列表"""
    tasks = task_service.get_tasks(
        db, 
        skip=skip, 
        limit=limit, 
        status=status,
        user_id=current_user.id
    )
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取任务详情"""
    task = task_service.get_task(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    return task

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """创建新任务（仅项目经理）"""
    task = task_service.create_task(db, task_in, creator_id=current_user.id)
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新任务"""
    task = task_service.get_task(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 权限检查：只有创建者或管理员可以更新
    if task.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此任务"
        )
    
    task = task_service.update_task(db, task=task, task_in=task_in)
    return task

@router.post("/{task_id}/claim", response_model=TaskResponse)
async def claim_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """认领任务"""
    task = task_service.claim_task(db, task_id=task_id, user_id=current_user.id)
    return task

@router.post("/{task_id}/submit", response_model=TaskResponse)
async def submit_task(
    task_id: int,
    actual_man_days: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """提交任务（填写实际投入人天）"""
    task = task_service.submit_task(
        db, 
        task_id=task_id, 
        user_id=current_user.id,
        actual_man_days=actual_man_days
    )
    return task

@router.post("/{task_id}/confirm", response_model=TaskResponse)
async def confirm_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_manager)
):
    """确认任务（仅项目经理）"""
    task = task_service.confirm_task(db, task_id=task_id)
    return task
```

### 依赖注入

#### 依赖函数设计
- 使用FastAPI的`Depends`进行依赖注入
- 数据库会话通过依赖注入管理
- 用户认证通过依赖注入验证

#### 依赖示例

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_token
from app.models.user import User
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """获取当前用户依赖"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    return user

def get_current_manager(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前项目经理依赖"""
    if not current_user.is_manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要项目经理权限"
        )
    return current_user

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前管理员依赖"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user
```

### 配置管理

#### 配置类设计
- 使用Pydantic的`BaseSettings`管理配置
- 从环境变量读取配置
- 提供默认值和类型验证

#### 配置示例

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "DevTeam Manager API"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # 数据库配置
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[str] = None
    
    @property
    def database_url(self) -> str:
        """构建数据库URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    # SQLite配置（开发环境）
    SQLITE_DB: str = "devteam_manager.db"
    
    # JWT配置
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30天
    
    # Redis配置（可选）
    REDIS_URL: Optional[str] = None
    
    # CORS配置
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 数据库模型

#### 模型设计规范
- 继承自`Base`模型（SQLAlchemy declarative_base）
- 使用类型注解
- 定义关系（relationship）
- 使用枚举类型定义状态字段

#### 模型示例

```python
# app/models/task.py
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.models.base import Base

class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    DRAFT = "draft"           # 草稿
    PUBLISHED = "published"   # 已发布
    CLAIMED = "claimed"       # 已认领
    IN_PROGRESS = "in_progress"  # 进行中
    SUBMITTED = "submitted"   # 已提交
    CONFIRMED = "confirmed"   # 已确认
    ARCHIVED = "archived"     # 已归档

class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="任务标题")
    description = Column(Text, comment="任务描述")
    status = Column(
        Enum(TaskStatus),
        default=TaskStatus.DRAFT,
        nullable=False,
        comment="任务状态"
    )
    estimated_man_days = Column(Float, nullable=False, comment="拟投入人天")
    actual_man_days = Column(Float, nullable=True, comment="实际投入人天")
    
    # 外键关系
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="认领者ID")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="完成时间")
    
    # 关系
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
```

### 业务逻辑服务

#### 服务层设计
- 业务逻辑集中在service层
- 服务层不直接处理HTTP请求/响应
- 使用类型注解提高代码可读性
- 异常处理统一管理

#### 服务示例

```python
# app/services/task_service.py
from sqlalchemy.orm import Session
from typing import Optional, List
from fastapi import HTTPException, status

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate

class TaskService:
    """任务服务"""
    
    def get_tasks(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> List[Task]:
        """获取任务列表"""
        query = db.query(Task)
        
        if status:
            query = query.filter(Task.status == status)
        
        if user_id:
            query = query.filter(
                (Task.creator_id == user_id) | (Task.assignee_id == user_id)
            )
        
        return query.offset(skip).limit(limit).all()
    
    def get_task(self, db: Session, task_id: int) -> Optional[Task]:
        """获取任务详情"""
        return db.query(Task).filter(Task.id == task_id).first()
    
    def create_task(
        self,
        db: Session,
        task_in: TaskCreate,
        creator_id: int
    ) -> Task:
        """创建任务"""
        task = Task(
            **task_in.dict(),
            creator_id=creator_id,
            status=TaskStatus.DRAFT
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    def update_task(
        self,
        db: Session,
        task: Task,
        task_in: TaskUpdate
    ) -> Task:
        """更新任务"""
        update_data = task_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    def claim_task(
        self,
        db: Session,
        task_id: int,
        user_id: int
    ) -> Task:
        """认领任务"""
        task = self.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        if task.status != TaskStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务状态为{task.status}，无法认领"
            )
        
        task.assignee_id = user_id
        task.status = TaskStatus.CLAIMED
        db.commit()
        db.refresh(task)
        return task
    
    def submit_task(
        self,
        db: Session,
        task_id: int,
        user_id: int,
        actual_man_days: float
    ) -> Task:
        """提交任务"""
        task = self.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        if task.assignee_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能提交自己认领的任务"
            )
        
        if task.status not in [TaskStatus.CLAIMED, TaskStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务状态为{task.status}，无法提交"
            )
        
        task.actual_man_days = actual_man_days
        task.status = TaskStatus.SUBMITTED
        db.commit()
        db.refresh(task)
        return task
    
    def confirm_task(
        self,
        db: Session,
        task_id: int
    ) -> Task:
        """确认任务（数据汇入统计）"""
        task = self.get_task(db, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )
        
        if task.status != TaskStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务状态为{task.status}，无法确认"
            )
        
        if not task.actual_man_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="任务未填写实际投入人天，无法确认"
            )
        
        task.status = TaskStatus.CONFIRMED
        task.completed_at = func.now()
        db.commit()
        db.refresh(task)
        
        # TODO: 将实际投入人天汇入开发者工作量统计
        # 这里可以触发一个后台任务或直接更新统计表
        
        return task

task_service = TaskService()
```

### Pydantic模式

#### Schema设计规范
- 请求和响应模式分离
- 使用类型注解
- 提供字段验证和默认值

#### Schema示例

```python
# app/schemas/task.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.task import TaskStatus

class TaskBase(BaseModel):
    """任务基础模式"""
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, max_length=2000, description="任务描述")
    estimated_man_days: float = Field(..., gt=0, description="拟投入人天")

class TaskCreate(TaskBase):
    """创建任务请求模式"""
    pass

class TaskUpdate(BaseModel):
    """更新任务请求模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    estimated_man_days: Optional[float] = Field(None, gt=0)
    status: Optional[TaskStatus] = None

class TaskResponse(TaskBase):
    """任务响应模式"""
    id: int
    status: TaskStatus
    actual_man_days: Optional[float] = None
    creator_id: int
    assignee_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

---

## 测试规范

### 测试结构
- 使用Pytest作为测试框架
- 测试文件与源代码结构对应
- 使用fixture管理测试数据
- 测试覆盖API、服务、模型各层

### 测试示例

```python
# tests/test_api/test_tasks.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.task import Task, TaskStatus

def test_create_task(
    client: TestClient,
    manager_token_headers: dict,
    db: Session
):
    """测试创建任务"""
    data = {
        "title": "测试任务",
        "description": "这是一个测试任务",
        "estimated_man_days": 3.5
    }
    response = client.post(
        f"{settings.API_V1_STR}/tasks/",
        headers=manager_token_headers,
        json=data
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["status"] == TaskStatus.DRAFT.value
    assert content["estimated_man_days"] == data["estimated_man_days"]

def test_claim_task(
    client: TestClient,
    developer_token_headers: dict,
    db: Session,
    published_task: Task
):
    """测试认领任务"""
    response = client.post(
        f"{settings.API_V1_STR}/tasks/{published_task.id}/claim",
        headers=developer_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == TaskStatus.CLAIMED.value

def test_submit_task(
    client: TestClient,
    developer_token_headers: dict,
    db: Session,
    claimed_task: Task
):
    """测试提交任务"""
    response = client.post(
        f"{settings.API_V1_STR}/tasks/{claimed_task.id}/submit",
        headers=developer_token_headers,
        params={"actual_man_days": 4.0}
    )
    assert response.status_code == 200
    content = response.json()
    assert content["status"] == TaskStatus.SUBMITTED.value
    assert content["actual_man_days"] == 4.0

# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import SessionLocal
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.core.security import create_access_token

@pytest.fixture
def db():
    """数据库会话fixture"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client():
    """测试客户端fixture"""
    return TestClient(app)

@pytest.fixture
def manager_user(db: Session) -> User:
    """创建项目经理用户"""
    user = User(
        username="manager",
        email="manager@example.com",
        hashed_password="hashed",
        is_manager=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def manager_token_headers(manager_user: User) -> dict:
    """项目经理token headers"""
    token = create_access_token(subject=manager_user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def published_task(db: Session, manager_user: User) -> Task:
    """创建已发布的任务"""
    task = Task(
        title="测试任务",
        description="测试描述",
        estimated_man_days=3.0,
        creator_id=manager_user.id,
        status=TaskStatus.PUBLISHED
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
```

---

## 部署配置

### Docker Compose配置

```yaml
# docker-compose.yml (开发环境)
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: devteam
      POSTGRES_PASSWORD: devteam123
      POSTGRES_DB: devteam_manager
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devteam"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://devteam:devteam123@postgres:5432/devteam_manager
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: your-secret-key-here
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

volumes:
  postgres_data:
```

### Dockerfile示例

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements/prod.txt requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 开发流程

### 环境变量配置

创建`.env.example`文件：

```env
# .env.example
# 应用配置
APP_NAME=DevTeam Manager API
API_V1_STR=/api/v1
DEBUG=True

# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_USER=devteam
POSTGRES_PASSWORD=devteam123
POSTGRES_DB=devteam_manager
DATABASE_URL=postgresql://devteam:devteam123@localhost:5432/devteam_manager

# JWT配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200

# Redis配置（可选）
REDIS_URL=redis://localhost:6379/0

# CORS配置
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### 开发命令

```bash
# 安装依赖
pip install -r requirements/dev.txt

# 运行开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 数据库迁移
# 生成迁移文件
alembic revision --autogenerate -m "描述信息"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 运行测试
pytest

# 运行测试并显示覆盖率
pytest --cov=app --cov-report=html

# 代码格式化
black .

# 导入排序
isort .

# 类型检查（可选）
mypy app
```

### 数据库迁移流程

1. **修改模型**：在`app/models/`中修改或添加模型
2. **生成迁移**：`alembic revision --autogenerate -m "描述"`
3. **检查迁移**：检查生成的迁移文件是否正确
4. **执行迁移**：`alembic upgrade head`
5. **测试验证**：运行测试确保迁移正确

### Git工作流
- **分支命名**：`feature/xxx`、`bugfix/xxx`、`hotfix/xxx`
- **提交规范**：使用Conventional Commits规范
- **代码审查**：所有代码必须经过Code Review

---

## 更新日志

| 版本 | 日期 | 更新内容 | 负责人 |
|------|------|----------|--------|
| v1.0 | 2024-05 | 初始版本，制定后端开发规范 | 后端组 |

---

**文档维护**：本文档随后端技术栈发展持续更新，重大变更需团队评审。
