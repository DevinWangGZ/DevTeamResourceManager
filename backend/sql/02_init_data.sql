-- DevTeam Manager 初始化数据脚本
-- 版本: v1.0
-- 创建日期: 2024-05

-- ============================================
-- 初始化测试数据
-- ============================================

-- 注意：密码哈希值需要在实际使用时通过应用生成
-- 这里使用示例哈希值，实际部署时需要替换

-- 插入测试用户（密码均为: password123）
-- 密码哈希使用 bcrypt，示例哈希值（实际使用时需要应用生成）
INSERT INTO users (username, email, password_hash, full_name, role, status_tag) VALUES
    ('admin', 'admin@devteam.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJ5q5q5q5', '系统管理员', 'system_admin', '🔧系统维护'),
    ('pm001', 'pm001@devteam.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJ5q5q5q5', '项目经理1', 'project_manager', '📊项目管理'),
    ('lead001', 'lead001@devteam.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJ5q5q5q5', '开发组长1', 'development_lead', '👥团队管理'),
    ('dev001', 'dev001@devteam.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJ5q5q5q5', '开发人员1', 'developer', '🚀火力全开'),
    ('dev002', 'dev002@devteam.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJ5q5q5q5', '开发人员2', 'developer', '💻编码中'),
    ('dev003', 'dev003@devteam.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqJ5q5q5q5', '开发人员3', 'developer', '😴休息中')
ON CONFLICT (username) DO NOTHING;

-- 插入测试项目
INSERT INTO projects (name, description, estimated_output_value, created_by) VALUES
    ('项目A', '项目A描述', 100000.00, (SELECT id FROM users WHERE username = 'pm001')),
    ('项目B', '项目B描述', 200000.00, (SELECT id FROM users WHERE username = 'pm001')),
    ('项目C', '项目C描述', 150000.00, (SELECT id FROM users WHERE username = 'pm001'))
ON CONFLICT (name) DO NOTHING;

-- 插入测试技能
INSERT INTO skills (user_id, name, proficiency) VALUES
    ((SELECT id FROM users WHERE username = 'dev001'), 'Python', 'expert'),
    ((SELECT id FROM users WHERE username = 'dev001'), 'Vue.js', 'proficient'),
    ((SELECT id FROM users WHERE username = 'dev001'), 'PostgreSQL', 'familiar'),
    ((SELECT id FROM users WHERE username = 'dev002'), 'Java', 'expert'),
    ((SELECT id FROM users WHERE username = 'dev002'), 'Spring Boot', 'proficient'),
    ((SELECT id FROM users WHERE username = 'dev002'), 'MySQL', 'proficient'),
    ((SELECT id FROM users WHERE username = 'dev003'), 'JavaScript', 'expert'),
    ((SELECT id FROM users WHERE username = 'dev003'), 'React', 'proficient'),
    ((SELECT id FROM users WHERE username = 'dev003'), 'Node.js', 'familiar')
ON CONFLICT (user_id, name) DO NOTHING;

-- 插入测试业务履历
INSERT INTO experiences (user_id, project, module, role, description, man_days) VALUES
    ((SELECT id FROM users WHERE username = 'dev001'), '项目A', '用户模块', '后端开发', '负责用户认证和权限管理', 15.5),
    ((SELECT id FROM users WHERE username = 'dev001'), '项目B', '订单模块', '后端开发', '负责订单创建和支付流程', 20.0),
    ((SELECT id FROM users WHERE username = 'dev002'), '项目A', '商品模块', '后端开发', '负责商品管理和库存系统', 18.0),
    ((SELECT id FROM users WHERE username = 'dev003'), '项目B', '前端页面', '前端开发', '负责用户界面开发', 25.0)
ON CONFLICT DO NOTHING;

-- 插入测试序列管理
INSERT INTO user_sequences (user_id, level, unit_price) VALUES
    ((SELECT id FROM users WHERE username = 'dev001'), '高级开发', 2500.00),
    ((SELECT id FROM users WHERE username = 'dev002'), '中级开发', 2000.00),
    ((SELECT id FROM users WHERE username = 'dev003'), '初级开发', 1500.00)
ON CONFLICT (user_id, level) DO NOTHING;

-- 插入测试任务
INSERT INTO tasks (title, description, status, project_id, creator_id, assignee_id, estimated_man_days, required_skills) VALUES
    ('任务1：用户登录功能', '实现用户登录功能，包括JWT认证', 'published', 
     (SELECT id FROM projects WHERE name = '项目A'),
     (SELECT id FROM users WHERE username = 'pm001'),
     NULL, 5.0, 'Python, FastAPI'),
    ('任务2：商品列表展示', '实现商品列表页面，支持分页和筛选', 'claimed',
     (SELECT id FROM projects WHERE name = '项目A'),
     (SELECT id FROM users WHERE username = 'pm001'),
     (SELECT id FROM users WHERE username = 'dev001'), 8.0, 'Vue.js, Element Plus'),
    ('任务3：订单支付流程', '实现订单支付功能，集成第三方支付', 'submitted',
     (SELECT id FROM projects WHERE name = '项目B'),
     (SELECT id FROM users WHERE username = 'pm001'),
     (SELECT id FROM users WHERE username = 'dev002'), 10.0, 'Java, Spring Boot')
ON CONFLICT DO NOTHING;

-- 插入测试节假日（示例：2024年部分节假日）
INSERT INTO holidays (date, description, is_weekend) VALUES
    ('2024-01-01', '元旦', FALSE),
    ('2024-02-10', '春节', FALSE),
    ('2024-02-11', '春节', FALSE),
    ('2024-02-12', '春节', FALSE),
    ('2024-04-04', '清明节', FALSE),
    ('2024-05-01', '劳动节', FALSE),
    ('2024-06-10', '端午节', FALSE),
    ('2024-09-15', '中秋节', FALSE),
    ('2024-10-01', '国庆节', FALSE),
    ('2024-10-02', '国庆节', FALSE),
    ('2024-10-03', '国庆节', FALSE)
ON CONFLICT (date) DO NOTHING;

-- 初始化项目产值统计
INSERT INTO project_output_values (project_id, task_output_value, allocated_output_value) VALUES
    ((SELECT id FROM projects WHERE name = '项目A'), 0, 0),
    ((SELECT id FROM projects WHERE name = '项目B'), 0, 0),
    ((SELECT id FROM projects WHERE name = '项目C'), 0, 0)
ON CONFLICT (project_id) DO NOTHING;
