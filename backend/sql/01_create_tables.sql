-- DevTeam Manager 数据库建表语句
-- 版本: v1.0
-- 创建日期: 2024-05

-- ============================================
-- 1. 用户表 (users)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'developer' CHECK (role IN ('developer', 'project_manager', 'development_lead', 'system_admin')),
    status_tag VARCHAR(50),  -- 趣味化情绪标签，如 "🚀火力全开"
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 用户表索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);

COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.role IS '用户角色: developer(开发人员), project_manager(项目经理), development_lead(开发组长), system_admin(系统管理员)';
COMMENT ON COLUMN users.status_tag IS '趣味化情绪标签，如 "🚀火力全开"';

-- ============================================
-- 2. 技能表 (skills)
-- ============================================
CREATE TABLE IF NOT EXISTS skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    proficiency VARCHAR(20) NOT NULL CHECK (proficiency IN ('familiar', 'proficient', 'expert')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- 技能表索引
CREATE INDEX idx_skills_user_id ON skills(user_id);
CREATE INDEX idx_skills_name ON skills(name);

COMMENT ON TABLE skills IS '用户技能表';
COMMENT ON COLUMN skills.proficiency IS '熟练度: familiar(熟悉), proficient(熟练), expert(精通)';

-- ============================================
-- 3. 业务履历表 (experiences)
-- ============================================
CREATE TABLE IF NOT EXISTS experiences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project VARCHAR(100) NOT NULL,
    module VARCHAR(100),
    role VARCHAR(50),
    description TEXT,
    man_days DECIMAL(10, 2) NOT NULL DEFAULT 0,  -- 投入人天，支持小数
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 业务履历表索引
CREATE INDEX idx_experiences_user_id ON experiences(user_id);
CREATE INDEX idx_experiences_project ON experiences(project);

COMMENT ON TABLE experiences IS '用户业务履历表';
COMMENT ON COLUMN experiences.man_days IS '投入人天，支持小数（如0.5天）';

-- ============================================
-- 4. 项目表 (projects)
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    estimated_output_value DECIMAL(15, 2),  -- 预计产值（元）
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 项目表索引
CREATE INDEX idx_projects_name ON projects(name);
CREATE INDEX idx_projects_created_by ON projects(created_by);

COMMENT ON TABLE projects IS '项目表';
COMMENT ON COLUMN projects.estimated_output_value IS '预计产值（元），项目立项时填写';

-- ============================================
-- 5. 任务表 (tasks)
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft',           -- 草稿
        'published',       -- 已发布
        'pending_eval',    -- 待评估（派发任务时）
        'claimed',         -- 已认领
        'in_progress',     -- 进行中
        'submitted',       -- 已提交
        'confirmed',       -- 已确认
        'archived'         -- 已归档
    )),
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    creator_id INTEGER NOT NULL REFERENCES users(id),  -- 创建者（通常是PM）
    assignee_id INTEGER REFERENCES users(id),  -- 认领人/分配人
    estimated_man_days DECIMAL(10, 2) NOT NULL DEFAULT 0,  -- 拟投入人天（PM填写）
    actual_man_days DECIMAL(10, 2),  -- 实际投入人天（开发者填写）
    required_skills TEXT,  -- 所需技能（JSON格式或逗号分隔）
    deadline DATE,
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,  -- 是否置顶
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 任务表索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_creator_id ON tasks(creator_id);
CREATE INDEX idx_tasks_assignee_id ON tasks(assignee_id);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);

COMMENT ON TABLE tasks IS '任务表';
COMMENT ON COLUMN tasks.status IS '任务状态: draft(草稿), published(已发布), pending_eval(待评估), claimed(已认领), in_progress(进行中), submitted(已提交), confirmed(已确认), archived(已归档)';
COMMENT ON COLUMN tasks.estimated_man_days IS '拟投入人天，由PM填写';
COMMENT ON COLUMN tasks.actual_man_days IS '实际投入人天，由开发者填写';
COMMENT ON COLUMN tasks.is_pinned IS '是否置顶，用于任务优先级管理';

-- ============================================
-- 6. 序列管理表 (user_sequences)
-- ============================================
CREATE TABLE IF NOT EXISTS user_sequences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    level VARCHAR(50) NOT NULL,  -- 序列等级，如：初级开发、中级开发、高级开发
    unit_price DECIMAL(10, 2) NOT NULL,  -- 单价（元/人天）
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, level)
);

-- 序列管理表索引
CREATE INDEX idx_user_sequences_user_id ON user_sequences(user_id);

COMMENT ON TABLE user_sequences IS '用户序列管理表';
COMMENT ON COLUMN user_sequences.level IS '序列等级，如：初级开发、中级开发、高级开发';
COMMENT ON COLUMN user_sequences.unit_price IS '单价（元/人天），用于产值计算';

-- ============================================
-- 7. 任务排期表 (task_schedules)
-- ============================================
CREATE TABLE IF NOT EXISTS task_schedules (
    id SERIAL PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,  -- 预计开始日期
    end_date DATE NOT NULL,    -- 预计结束日期
    is_pinned BOOLEAN NOT NULL DEFAULT FALSE,  -- 是否置顶
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id)
);

-- 任务排期表索引
CREATE INDEX idx_task_schedules_task_id ON task_schedules(task_id);
CREATE INDEX idx_task_schedules_start_date ON task_schedules(start_date);
CREATE INDEX idx_task_schedules_end_date ON task_schedules(end_date);

COMMENT ON TABLE task_schedules IS '任务排期表，用于自动排期功能';
COMMENT ON COLUMN task_schedules.start_date IS '预计开始日期（工作日）';
COMMENT ON COLUMN task_schedules.end_date IS '预计结束日期（工作日）';

-- ============================================
-- 8. 节假日表 (holidays)
-- ============================================
CREATE TABLE IF NOT EXISTS holidays (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    description VARCHAR(200),  -- 节假日描述，如：春节、国庆节
    is_weekend BOOLEAN NOT NULL DEFAULT FALSE,  -- 是否为周末
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 节假日表索引
CREATE INDEX idx_holidays_date ON holidays(date);

COMMENT ON TABLE holidays IS '节假日表，用于排期计算时排除节假日';
COMMENT ON COLUMN holidays.is_weekend IS '是否为周末，周末自动排除';

-- ============================================
-- 9. 项目产值统计表 (project_output_values)
-- ============================================
CREATE TABLE IF NOT EXISTS project_output_values (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_output_value DECIMAL(15, 2) NOT NULL DEFAULT 0,  -- 任务产值（已完成+未完成）
    allocated_output_value DECIMAL(15, 2) NOT NULL DEFAULT 0,  -- 已分配产值（已完成任务）
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id)
);

-- 项目产值统计表索引
CREATE INDEX idx_project_output_values_project_id ON project_output_values(project_id);

COMMENT ON TABLE project_output_values IS '项目产值统计表';
COMMENT ON COLUMN project_output_values.task_output_value IS '任务产值 = Σ(任务的实际投入人天 × 开发人员的序列单价)，包含已完成和未完成';
COMMENT ON COLUMN project_output_values.allocated_output_value IS '已分配产值 = Σ(已确认任务的实际投入人天 × 开发人员的序列单价)';

-- ============================================
-- 10. 工作量统计表 (workload_statistics)
-- ============================================
CREATE TABLE IF NOT EXISTS workload_statistics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    total_man_days DECIMAL(10, 2) NOT NULL DEFAULT 0,  -- 总投入人天
    period_start DATE NOT NULL,  -- 统计周期开始日期
    period_end DATE NOT NULL,    -- 统计周期结束日期
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 工作量统计表索引
CREATE INDEX idx_workload_statistics_user_id ON workload_statistics(user_id);
CREATE INDEX idx_workload_statistics_project_id ON workload_statistics(project_id);
CREATE INDEX idx_workload_statistics_period ON workload_statistics(period_start, period_end);

COMMENT ON TABLE workload_statistics IS '工作量统计表，基于任务确认后的实际投入人天';
COMMENT ON COLUMN workload_statistics.total_man_days IS '总投入人天，来自已确认任务的实际投入人天';

-- ============================================
-- 11. 知识分享表 (articles) - 后续功能
-- ============================================
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,  -- Markdown格式内容
    author_id INTEGER NOT NULL REFERENCES users(id),
    category VARCHAR(50),  -- 分类
    tags TEXT,  -- 标签（JSON格式或逗号分隔）
    is_published BOOLEAN NOT NULL DEFAULT FALSE,  -- 是否发布
    view_count INTEGER NOT NULL DEFAULT 0,  -- 浏览次数
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 知识分享表索引
CREATE INDEX idx_articles_author_id ON articles(author_id);
CREATE INDEX idx_articles_is_published ON articles(is_published);
CREATE INDEX idx_articles_created_at ON articles(created_at);

COMMENT ON TABLE articles IS '知识分享表，支持Markdown格式';
COMMENT ON COLUMN articles.content IS '文章内容，Markdown格式';

-- ============================================
-- 12. 消息通知表 (messages) - 后续功能
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    type VARCHAR(50) NOT NULL,  -- 消息类型：task_status_change, todo_reminder, system_notice
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    related_task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 消息通知表索引
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_is_read ON messages(is_read);
CREATE INDEX idx_messages_created_at ON messages(created_at);

COMMENT ON TABLE messages IS '消息通知表';
COMMENT ON COLUMN messages.type IS '消息类型: task_status_change(任务状态变更), todo_reminder(待办提醒), system_notice(系统通知)';

-- ============================================
-- 更新时间触发器函数
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为需要的表创建更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_skills_updated_at BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_experiences_updated_at BEFORE UPDATE ON experiences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_sequences_updated_at BEFORE UPDATE ON user_sequences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_schedules_updated_at BEFORE UPDATE ON task_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workload_statistics_updated_at BEFORE UPDATE ON workload_statistics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
