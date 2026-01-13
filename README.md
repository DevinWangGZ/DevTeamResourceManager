# DevTeam Manager

> **极简、透明、自助**的内部开发者资源管理与协作平台

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.4+-green.svg)](https://vuejs.org/)

## 📖 项目简介

DevTeam Manager 是一个专为开发团队设计的资源管理与协作平台，旨在解决团队资源匹配、任务分发与工作量量化等核心痛点。

### 核心特性

- 🎯 **极简设计**：功能以解决核心痛点为准，避免过度设计
- 🚫 **去审批化**：以"公开透明"和"事后确认"保障数据质量
- 😊 **用户友好**：注重开发人员填报体验，降低抵触情绪
- 📊 **数据驱动**：所有分析基于"投入人天"等客观数据
- 🤝 **信任为先**：默认信任用户填报，通过同伴监督纠偏

## 🏗️ 技术栈

### 前端
- **Vue 3.4+** - 渐进式JavaScript框架
- **TypeScript 5.3+** - 类型安全的JavaScript
- **Vite 5.0+** - 下一代前端构建工具
- **Element Plus 2.4+** - Vue 3组件库
- **Pinia 2.1+** - 状态管理
- **ECharts 5.4+** - 数据可视化

### 后端
- **Python 3.12** - 编程语言
- **FastAPI 0.104+** - 现代Web框架
- **SQLAlchemy 2.0+** - ORM框架
- **PostgreSQL 15+** - 关系型数据库
- **Alembic 1.13+** - 数据库迁移工具

## 🚀 快速开始

### 环境要求

- Node.js 18.0+
- Python 3.12+ (当前使用 3.13.9)
- PostgreSQL 15+（生产环境）或 SQLite（开发环境）
- Docker & Docker Compose（可选，用于PostgreSQL）

### 快速启动

**详细步骤请参考**：[快速启动指南](./SETUP.md)

#### 使用Makefile（推荐）

```bash
# 安装所有依赖
make install

# 启动后端（新终端）
make dev-backend

# 启动前端（新终端）
make dev-frontend
```

#### 手动启动

**后端：**
```bash
cd backend
pip install -r requirements/dev.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**
```bash
cd frontend
npm install
cp .env.example .env.development
npm run dev
```

### 访问应用

- **前端**：http://localhost:5173
- **后端API**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

## 📁 项目结构

```
DevTeamResourceManager/
├── backend/              # 后端代码
│   ├── app/             # 应用代码
│   ├── alembic/         # 数据库迁移
│   ├── tests/           # 测试代码
│   └── requirements/    # 依赖管理
├── frontend/            # 前端代码
│   ├── src/            # 源代码
│   ├── public/         # 静态资源
│   └── tests/          # 测试代码
├── docs/                # 项目文档
│   ├── RULES.md        # 项目规则
│   ├── FRONTEND_RULES.md # 前端规范
│   ├── BACKEND_RULES.md  # 后端规范
│   ├── DEVELOPMENT_GUIDE.md # 开发指南
│   └── requirements/   # 需求文档
│       ├── SPECIFICATION.md # 需求规格说明书
│       └── USER_STORIES.md  # 用户故事
└── README.md           # 项目说明
```

## 📚 文档

### 开发规范
- [项目开发规范](./docs/RULES.md)
- [前端开发规范](./docs/FRONTEND_RULES.md)
- [后端开发规范](./docs/BACKEND_RULES.md)
- [开发指南](./docs/DEVELOPMENT_GUIDE.md)

### 需求文档
- [需求规格说明书](./docs/requirements/SPECIFICATION.md)
- [用户故事](./docs/requirements/USER_STORIES.md)
- [实施路线图](./docs/IMPLEMENTATION_ROADMAP.md)

## 🧪 测试

### 后端测试
```bash
cd backend
pytest
pytest --cov=app --cov-report=html
```

### 前端测试
```bash
cd frontend
npm run test:unit
```

## 🤝 贡献指南

欢迎贡献代码！请阅读[开发指南](./docs/DEVELOPMENT_GUIDE.md)了解：

- Git工作流
- 代码提交规范
- 代码审查流程

## 📝 功能优先级

### P0（核心功能）
- ✅ 用户认证与角色管理
- ✅ 任务系统（发布、认领、提交、确认）
- ✅ 人员档案管理（技能、履历）
- ✅ 工作量统计（基于实际投入人天）

### P1（重要功能）
- ⏳ 负荷可视化（个人/团队）
- ⏳ 任务集市（浏览、筛选、认领）
- ⏳ 管理仪表盘（团队指标、待办提醒）
- ⏳ 绩效数据可视化

### P2（增强功能）
- 📋 智能匹配（基于需求的候选人推荐）
- 📋 团队能力洞察（技能矩阵、人才梯队分析）
- 📋 数据导出功能
- 📋 消息通知系统

## 📄 许可证

[MIT License](LICENSE)

## 👥 团队

项目由开发团队共同维护。

---

**文档版本**：v1.0 | **更新日期**：2024-05
