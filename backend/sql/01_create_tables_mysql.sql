-- DevTeam Manager 数据库建表语句 (MySQL版本)
-- 版本: v1.0
-- 创建日期: 2024-05
-- 数据库: devteam_manager
-- 注意: 需要MySQL 5.7+或8.0+，使用InnoDB存储引擎
-- 文件编码: UTF-8

-- 设置客户端连接字符集为UTF-8
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4;

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS devteam_manager DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE devteam_manager;

-- 确保当前会话使用UTF-8
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4;

-- ============================================
-- 1. 用户表 (users)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    full_name VARCHAR(100) COMMENT '全名',
    role VARCHAR(20) NOT NULL DEFAULT 'developer' COMMENT '用户角色: developer(开发人员), project_manager(项目经理), development_lead(开发组长), system_admin(系统管理员)',
    status_tag VARCHAR(50) COMMENT '趣味化情绪标签，如 "🚀火力全开"',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否激活',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_users_email (email),
    INDEX idx_users_username (username),
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ============================================
-- 2. 技能表 (skills)
-- ============================================
CREATE TABLE IF NOT EXISTS skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    name VARCHAR(100) NOT NULL COMMENT '技能名称',
    proficiency VARCHAR(20) NOT NULL COMMENT '熟练度: familiar(熟悉), proficient(熟练), expert(精通)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uq_user_skill (user_id, name),
    INDEX idx_skills_user_id (user_id),
    INDEX idx_skills_name (name),
    CONSTRAINT fk_skills_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户技能表';

-- ============================================
-- 3. 业务履历表 (experiences)
-- ============================================
CREATE TABLE IF NOT EXISTS experiences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    project VARCHAR(100) NOT NULL COMMENT '项目名称',
    module VARCHAR(100) COMMENT '模块名称',
    role VARCHAR(50) COMMENT '角色',
    description TEXT COMMENT '贡献描述',
    man_days DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '投入人天，支持小数（如0.5天）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_experiences_user_id (user_id),
    INDEX idx_experiences_project (project),
    CONSTRAINT fk_experiences_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户业务履历表';

-- ============================================
-- 4. 项目表 (projects)
-- ============================================
CREATE TABLE IF NOT EXISTS projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '项目名称',
    description TEXT COMMENT '项目描述',
    estimated_output_value DECIMAL(15, 2) COMMENT '预计产值（元），项目立项时填写',
    created_by INT COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_projects_name (name),
    INDEX idx_projects_created_by (created_by),
    CONSTRAINT fk_projects_created_by FOREIGN KEY (created_by) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目表';

-- ============================================
-- 5. 任务表 (tasks)
-- ============================================
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL COMMENT '任务标题',
    description TEXT COMMENT '任务描述',
    status VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT '任务状态: draft(草稿), published(已发布), pending_eval(待评估), claimed(已认领), in_progress(进行中), submitted(已提交), confirmed(已确认), archived(已归档)',
    project_id INT COMMENT '项目ID',
    creator_id INT NOT NULL COMMENT '创建者ID（通常是PM）',
    assignee_id INT COMMENT '认领人/分配人ID',
    estimated_man_days DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '拟投入人天，由PM填写',
    actual_man_days DECIMAL(10, 2) COMMENT '实际投入人天，由开发者填写',
    required_skills TEXT COMMENT '所需技能（JSON格式或逗号分隔）',
    deadline DATE COMMENT '截止日期',
    is_pinned TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否置顶，用于任务优先级管理',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_tasks_status (status),
    INDEX idx_tasks_project_id (project_id),
    INDEX idx_tasks_creator_id (creator_id),
    INDEX idx_tasks_assignee_id (assignee_id),
    INDEX idx_tasks_created_at (created_at),
    CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    CONSTRAINT fk_tasks_creator FOREIGN KEY (creator_id) REFERENCES users(id),
    CONSTRAINT fk_tasks_assignee FOREIGN KEY (assignee_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务表';

-- ============================================
-- 6. 序列管理表 (user_sequences)
-- ============================================
CREATE TABLE IF NOT EXISTS user_sequences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    level VARCHAR(50) NOT NULL COMMENT '序列等级，如：初级开发、中级开发、高级开发',
    unit_price DECIMAL(10, 2) NOT NULL COMMENT '单价（元/人天），用于产值计算',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uq_user_sequence (user_id, level),
    INDEX idx_user_sequences_user_id (user_id),
    CONSTRAINT fk_user_sequences_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户序列管理表';

-- ============================================
-- 7. 任务排期表 (task_schedules)
-- ============================================
CREATE TABLE IF NOT EXISTS task_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL UNIQUE COMMENT '任务ID',
    start_date DATE NOT NULL COMMENT '预计开始日期（工作日）',
    end_date DATE NOT NULL COMMENT '预计结束日期（工作日）',
    is_pinned TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否置顶',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_task_schedules_task_id (task_id),
    INDEX idx_task_schedules_start_date (start_date),
    INDEX idx_task_schedules_end_date (end_date),
    CONSTRAINT fk_task_schedules_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务排期表，用于自动排期功能';

-- ============================================
-- 8. 节假日表 (holidays)
-- ============================================
CREATE TABLE IF NOT EXISTS holidays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL UNIQUE COMMENT '日期',
    description VARCHAR(200) COMMENT '节假日描述，如：春节、国庆节',
    is_weekend TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为周末，周末自动排除',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_holidays_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='节假日表，用于排期计算时排除节假日';

-- ============================================
-- 9. 项目产值统计表 (project_output_values)
-- ============================================
CREATE TABLE IF NOT EXISTS project_output_values (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_id INT NOT NULL UNIQUE COMMENT '项目ID',
    task_output_value DECIMAL(15, 2) NOT NULL DEFAULT 0 COMMENT '任务产值 = Σ(任务的实际投入人天 × 开发人员的序列单价)，包含已完成和未完成',
    allocated_output_value DECIMAL(15, 2) NOT NULL DEFAULT 0 COMMENT '已分配产值 = Σ(已确认任务的实际投入人天 × 开发人员的序列单价)',
    calculated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '计算时间',
    INDEX idx_project_output_values_project_id (project_id),
    CONSTRAINT fk_project_output_values_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='项目产值统计表';

-- ============================================
-- 10. 工作量统计表 (workload_statistics)
-- ============================================
CREATE TABLE IF NOT EXISTS workload_statistics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    project_id INT COMMENT '项目ID',
    total_man_days DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '总投入人天，来自已确认任务的实际投入人天',
    period_start DATE NOT NULL COMMENT '统计周期开始日期',
    period_end DATE NOT NULL COMMENT '统计周期结束日期',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_workload_statistics_user_id (user_id),
    INDEX idx_workload_statistics_project_id (project_id),
    INDEX idx_workload_statistics_period (period_start, period_end),
    CONSTRAINT fk_workload_statistics_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_workload_statistics_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工作量统计表，基于任务确认后的实际投入人天';

-- ============================================
-- 11. 知识分享表 (articles) - 后续功能
-- ============================================
CREATE TABLE IF NOT EXISTS articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL COMMENT '文章标题',
    content TEXT NOT NULL COMMENT '文章内容，Markdown格式',
    author_id INT NOT NULL COMMENT '作者ID',
    category VARCHAR(50) COMMENT '分类',
    tags TEXT COMMENT '标签（JSON格式或逗号分隔）',
    is_published TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否发布',
    view_count INT NOT NULL DEFAULT 0 COMMENT '浏览次数',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_articles_author_id (author_id),
    INDEX idx_articles_is_published (is_published),
    INDEX idx_articles_created_at (created_at),
    CONSTRAINT fk_articles_author FOREIGN KEY (author_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识分享表，支持Markdown格式';

-- ============================================
-- 12. 消息通知表 (messages) - 后续功能
-- ============================================
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    title VARCHAR(200) NOT NULL COMMENT '消息标题',
    content TEXT COMMENT '消息内容',
    type VARCHAR(50) NOT NULL COMMENT '消息类型: task_status_change(任务状态变更), todo_reminder(待办提醒), system_notice(系统通知)',
    is_read TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已读',
    related_task_id INT COMMENT '关联任务ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_messages_user_id (user_id),
    INDEX idx_messages_is_read (is_read),
    INDEX idx_messages_created_at (created_at),
    CONSTRAINT fk_messages_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_messages_task FOREIGN KEY (related_task_id) REFERENCES tasks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息通知表';
