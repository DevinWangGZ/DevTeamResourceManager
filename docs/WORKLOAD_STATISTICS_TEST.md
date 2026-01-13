# 工作量统计功能测试指南

## 测试目标

验证当项目经理确认任务后，系统是否自动将任务的实际投入人天计入开发人员的工作量统计。

## 测试方法

### 方法一：通过前端界面测试（推荐）

#### 步骤1：准备测试数据

1. **登录开发人员账号**（如 `dev001` / `password123`）
2. **进入任务列表**，找到已认领或进行中的任务
3. **提交任务**：
   - 点击任务详情
   - 填写"实际投入人天"（如：5.0）
   - 点击"提交"按钮
   - 任务状态应变为"已提交"

#### 步骤2：确认任务

1. **登录项目经理账号**（如 `pm001` / `password123`）
2. **进入任务列表**，筛选状态为"已提交"的任务
3. **确认任务**：
   - 点击任务详情
   - 点击"确认"按钮
   - 任务状态应变为"已确认"

#### 步骤3：查看工作量统计

1. **登录开发人员账号**（如 `dev001` / `password123`）
2. **访问工作量统计页面**：
   - 从首页点击"工作量统计"按钮
   - 或直接访问 `/workload`
3. **验证统计结果**：
   - 查看"总投入人天"是否增加了任务的实际投入人天
   - 查看统计列表中是否有新的记录
   - 记录应包含正确的项目ID和统计周期

### 方法二：通过API测试

#### 步骤1：获取访问令牌

```bash
# 登录获取token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=dev001&password=password123"
```

保存返回的 `access_token`。

#### 步骤2：提交任务（如果还没有已提交的任务）

```bash
# 使用开发人员token提交任务
curl -X POST "http://localhost:8000/api/v1/tasks/TASK_ID/submit" \
  -H "Authorization: Bearer YOUR_DEV_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"actual_man_days": 5.0}'
```

#### 步骤3：确认任务

```bash
# 使用项目经理token确认任务
curl -X POST "http://localhost:8000/api/v1/tasks/TASK_ID/confirm" \
  -H "Authorization: Bearer YOUR_PM_TOKEN"
```

#### 步骤4：查看工作量统计

```bash
# 使用开发人员token查看统计
curl -X GET "http://localhost:8000/api/v1/workload-statistics/my" \
  -H "Authorization: Bearer YOUR_DEV_TOKEN"
```

### 方法三：使用SQL直接检查

#### 步骤1：查看已提交的任务

```sql
SELECT 
    id,
    title,
    status,
    assignee_id,
    project_id,
    actual_man_days
FROM tasks
WHERE status = 'submitted';
```

#### 步骤2：查看确认前的工作量统计

```sql
SELECT 
    id,
    user_id,
    project_id,
    total_man_days,
    period_start,
    period_end
FROM workload_statistics
WHERE user_id = (SELECT assignee_id FROM tasks WHERE status = 'submitted' LIMIT 1)
  AND project_id = (SELECT project_id FROM tasks WHERE status = 'submitted' LIMIT 1);
```

记录下总投入人天数。

#### 步骤3：确认任务（通过API或前端）

#### 步骤4：查看确认后的工作量统计

```sql
SELECT 
    id,
    user_id,
    project_id,
    total_man_days,
    period_start,
    period_end,
    created_at,
    updated_at
FROM workload_statistics
WHERE user_id = (SELECT assignee_id FROM tasks WHERE status = 'confirmed' LIMIT 1)
  AND project_id = (SELECT project_id FROM tasks WHERE status = 'confirmed' LIMIT 1);
```

#### 步骤5：验证结果

- 统计中的 `total_man_days` 应该增加了任务的实际投入人天
- 如果该周期和项目已有统计记录，则累加到现有记录
- 如果没有统计记录，则创建新记录

## 预期结果

1. ✅ **任务状态更新**：任务状态从 `submitted` 变为 `confirmed`
2. ✅ **统计记录创建/更新**：工作量统计表中新增或更新记录
3. ✅ **数据正确性**：
   - `user_id` = 任务的 `assignee_id`
   - `project_id` = 任务的 `project_id`
   - `total_man_days` = 任务的实际投入人天（或累加值）
   - `period_start` 和 `period_end` = 任务确认日期所在月份

## 验证检查清单

- [ ] 任务确认后，状态变为 `confirmed`
- [ ] 工作量统计表中出现新记录或更新现有记录
- [ ] 统计记录的 `user_id` 正确（任务认领人）
- [ ] 统计记录的 `project_id` 正确（任务所属项目）
- [ ] 统计记录的 `total_man_days` 正确（等于或累加任务的实际投入人天）
- [ ] 统计记录的周期正确（任务确认日期所在月份）
- [ ] 前端工作量统计页面显示更新后的数据

## 常见问题排查

### Q1: 确认任务后统计没有更新？

**检查清单：**
1. ✅ 任务是否有 `assignee_id`？（必须有认领人）
2. ✅ 任务是否有 `actual_man_days`？（必须有实际投入人天）
3. ✅ 任务是否有 `project_id`？（必须属于某个项目）
4. ✅ 后端服务是否正常运行？
5. ✅ 查看后端日志是否有错误信息
6. ✅ 检查 `task_service.py` 中的 `confirm_task` 方法是否调用了 `WorkloadStatisticService.update_statistic_on_task_confirmation`

### Q2: 统计记录是按什么周期创建的？

**A:** 默认按任务确认日期所在月份创建统计记录。

- 如果任务在 2024-01-15 确认，统计周期为 2024-01-01 ~ 2024-01-31
- 同一用户、同一项目、同一周期的统计会累加
- 例如：同一用户在同一项目的同一月份完成多个任务，统计会累加

### Q3: 如何查看所有工作量统计？

```sql
SELECT 
    ws.*,
    u.username,
    p.name as project_name
FROM workload_statistics ws
LEFT JOIN users u ON ws.user_id = u.id
LEFT JOIN projects p ON ws.project_id = p.id
ORDER BY ws.user_id, ws.project_id, ws.period_start DESC;
```

### Q4: 如何准备测试数据？

如果需要快速准备测试数据：

```sql
-- 1. 将第一个任务改为已提交状态
UPDATE tasks 
SET status = 'submitted', 
    actual_man_days = 5.0,
    assignee_id = (SELECT id FROM users WHERE username = 'dev001' LIMIT 1)
WHERE id = (SELECT id FROM tasks LIMIT 1);

-- 2. 验证准备情况
SELECT 
    t.id,
    t.title,
    t.status,
    t.assignee_id,
    t.project_id,
    t.actual_man_days,
    u.username as assignee_name
FROM tasks t
LEFT JOIN users u ON t.assignee_id = u.id
WHERE t.status = 'submitted';
```

## 测试脚本

如果需要在本地运行测试脚本（需要数据库连接权限）：

```bash
cd /Users/wangwenhao/Documents/work/code.nosync/DevTeamResourceManager
python scripts/test_workload_statistics.py
```

---

**文档维护**：本文档随功能更新持续维护。
