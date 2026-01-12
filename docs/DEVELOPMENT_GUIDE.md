# 开发指南

> **文档版本**：v1.0 | **更新日期**：2024-05 | **负责人**：项目组

## 目录
- [Git工作流](#git工作流)
- [代码提交规范](#代码提交规范)
- [代码审查流程](#代码审查流程)
- [分支管理策略](#分支管理策略)
- [环境配置](#环境配置)
- [常见问题](#常见问题)

---

## Git工作流

### 分支命名规范

- **feature/xxx**：新功能开发
  - 示例：`feature/task-market`、`feature/user-profile`
- **bugfix/xxx**：Bug修复
  - 示例：`bugfix/task-status-update`、`bugfix/login-error`
- **hotfix/xxx**：紧急修复（生产环境）
  - 示例：`hotfix/security-patch`、`hotfix/data-loss`
- **refactor/xxx**：代码重构
  - 示例：`refactor/api-structure`、`refactor/component-extract`
- **docs/xxx**：文档更新
  - 示例：`docs/api-docs`、`docs/setup-guide`
- **test/xxx**：测试相关
  - 示例：`test/task-service`、`test/e2e-setup`

### 工作流程

1. **创建分支**
   ```bash
   git checkout -b feature/task-market
   ```

2. **开发与提交**
   - 频繁提交，每次提交解决一个问题
   - 提交信息遵循[提交规范](#代码提交规范)
   - 保持代码可运行，不提交破坏性代码

3. **推送分支**
   ```bash
   git push origin feature/task-market
   ```

4. **创建Pull Request**
   - 在GitHub/GitLab等平台创建PR
   - 填写PR描述，说明改动内容
   - 关联相关Issue（如有）

5. **代码审查**
   - 等待审查者Review
   - 根据反馈修改代码
   - 审查通过后合并

6. **合并后清理**
   ```bash
   git checkout main
   git pull
   git branch -d feature/task-market
   ```

---

## 代码提交规范

### Conventional Commits规范

提交信息格式：
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type类型

- **feat**：新功能
  - 示例：`feat(task): 添加任务认领功能`
- **fix**：Bug修复
  - 示例：`fix(auth): 修复登录token过期问题`
- **docs**：文档更新
  - 示例：`docs(api): 更新API文档`
- **style**：代码格式调整（不影响功能）
  - 示例：`style(component): 格式化代码`
- **refactor**：代码重构
  - 示例：`refactor(service): 重构任务服务层`
- **perf**：性能优化
  - 示例：`perf(api): 优化任务列表查询性能`
- **test**：测试相关
  - 示例：`test(task): 添加任务服务单元测试`
- **chore**：构建/工具相关
  - 示例：`chore(deps): 更新依赖版本`
- **ci**：CI/CD相关
  - 示例：`ci(github): 添加GitHub Actions工作流`

### Scope范围（可选）

- 模块名：`task`、`auth`、`user`、`api`等
- 组件名：`TaskCard`、`UserProfile`等
- 文件名：`task-service.py`、`TaskMarket.vue`等

### Subject主题

- 使用祈使句，首字母小写
- 不超过50个字符
- 不包含句号

### Body正文（可选）

- 详细说明改动原因和方式
- 与上一行空一行
- 每行不超过72个字符

### Footer页脚（可选）

- 关联Issue：`Closes #123`
- 破坏性变更：`BREAKING CHANGE: 修改API接口`

### 提交示例

```bash
# 简单提交
git commit -m "feat(task): 添加任务认领功能"

# 详细提交
git commit -m "feat(task): 添加任务认领功能

- 实现任务认领API端点
- 添加任务状态流转验证
- 更新任务模型，添加认领者字段

Closes #123"
```

---

## 代码审查流程

### 审查前准备

1. **自检清单**
   - [ ] 代码可以正常运行
   - [ ] 通过所有测试
   - [ ] 遵循代码规范（ESLint/Black等）
   - [ ] 没有调试代码和注释
   - [ ] 更新了相关文档

2. **PR描述**
   - 清晰说明改动内容
   - 说明为什么需要这个改动
   - 提供测试步骤或截图
   - 关联相关Issue

### 审查要点

#### 功能正确性
- 代码是否实现了预期功能
- 边界情况是否处理
- 错误处理是否完善

#### 代码质量
- 代码是否清晰易读
- 是否遵循项目规范
- 是否有重复代码
- 命名是否合理

#### 性能与安全
- 是否有性能问题
- 是否有安全隐患
- 数据库查询是否优化

#### 测试覆盖
- 是否有足够的测试
- 测试是否通过
- 边界情况是否测试

### 审查反馈

- **必须修改**：使用`必须`或`必须修改`
- **建议修改**：使用`建议`或`可以考虑`
- **疑问**：使用`疑问`或`为什么`
- **表扬**：使用`很好`或`👍`

### 审查后处理

1. **根据反馈修改代码**
2. **重新提交并推送**
3. **在PR中回复审查者**
4. **审查通过后合并**

---

## 分支管理策略

### 主分支

- **main/master**：生产环境代码
  - 受保护，不能直接推送
  - 只能通过PR合并
  - 每次合并触发部署（如配置了CI/CD）

- **develop**：开发环境代码（可选）
  - 日常开发合并到此分支
  - 定期合并到main分支

### 功能分支

- 从`main`分支创建
- 开发完成后合并回`main`
- 合并后删除分支

### 发布分支（可选）

- **release/x.x.x**：准备发布版本
- 从`develop`创建
- 修复Bug，不添加新功能
- 测试通过后合并到`main`和`develop`

### 热修复分支

- **hotfix/xxx**：紧急修复生产Bug
- 从`main`创建
- 修复后合并到`main`和`develop`
- 立即发布

---

## 环境配置

### 开发环境要求

- **Node.js**：18.0+（前端）
- **Python**：3.12+（后端）
- **PostgreSQL**：15+（生产）或SQLite（开发）
- **Git**：2.30+

### 环境变量

#### 前端环境变量

创建`.env.development`：
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=DevTeam Manager (开发环境)
```

#### 后端环境变量

创建`.env`：
```env
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_USER=devteam
POSTGRES_PASSWORD=devteam123
POSTGRES_DB=devteam_manager

# JWT配置
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

### 首次设置

1. **克隆仓库**
   ```bash
   git clone <repository-url>
   cd DevTeamResourceManager
   ```

2. **前端设置**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.development
   npm run dev
   ```

3. **后端设置**
   ```bash
   cd backend
   pip install -r requirements/dev.txt
   cp .env.example .env
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

---

## 常见问题

### Git相关问题

**Q: 如何撤销最后一次提交？**
```bash
# 保留修改
git reset --soft HEAD~1

# 不保留修改
git reset --hard HEAD~1
```

**Q: 如何修改最后一次提交信息？**
```bash
git commit --amend -m "新的提交信息"
```

**Q: 如何合并多个提交？**
```bash
git rebase -i HEAD~n  # n为要合并的提交数
```

### 代码问题

**Q: 代码格式化失败怎么办？**
- 前端：运行`npm run lint --fix`
- 后端：运行`black .`和`isort .`

**Q: 测试失败怎么办？**
- 检查测试环境是否正确
- 检查数据库连接
- 查看测试日志

**Q: 依赖冲突怎么办？**
- 更新依赖版本
- 检查`package.json`或`requirements.txt`
- 删除`node_modules`或虚拟环境重新安装

---

## 更新日志

| 版本 | 日期 | 更新内容 | 负责人 |
|------|------|----------|--------|
| v1.0 | 2024-05 | 初始版本，制定开发指南 | 项目组 |

---

**文档维护**：本文档随项目发展持续更新，重大变更需团队评审。
