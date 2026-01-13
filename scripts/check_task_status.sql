-- 检查任务状态和准备测试数据
-- 用于测试工作量统计功能

USE devteam_manager;

-- 1. 查看所有任务的状态
SELECT 
    id,
    title,
    status,
    assignee_id,
    project_id,
    estimated_man_days,
    actual_man_days,
    created_at,
    updated_at
FROM tasks
ORDER BY id;

-- 2. 查看已提交状态的任务（可以确认的任务）
SELECT 
    id,
    title,
    status,
    assignee_id,
    project_id,
    actual_man_days
FROM tasks
WHERE status = 'submitted';

-- 3. 如果没有已提交的任务，可以手动创建一个测试任务
-- 注意：需要先有一个任务，然后将其状态改为submitted，并设置actual_man_days
-- 示例：将第一个任务改为已提交状态（如果有的话）
-- UPDATE tasks 
-- SET status = 'submitted', 
--     actual_man_days = 5.0,
--     assignee_id = (SELECT id FROM users WHERE username = 'dev001' LIMIT 1)
-- WHERE id = (SELECT id FROM tasks LIMIT 1);

-- 4. 查看当前的工作量统计
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
ORDER BY user_id, project_id, period_start DESC;

-- 5. 查看用户信息（用于确认任务）
SELECT 
    id,
    username,
    role
FROM users
WHERE role IN ('project_manager', 'system_admin');
