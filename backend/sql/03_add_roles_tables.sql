-- 添加角色表和用户角色关联表
-- 版本: v1.1
-- 创建日期: 2024-05
-- 说明: 支持用户多角色管理

USE devteam_manager;

-- ============================================
-- 1. 角色表 (roles)
-- ============================================
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名称',
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '角色代码',
    description TEXT COMMENT '角色描述',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_roles_code (code),
    INDEX idx_roles_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- ============================================
-- 2. 用户角色关联表 (user_roles)
-- ============================================
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INT NOT NULL COMMENT '用户ID',
    role_id INT NOT NULL COMMENT '角色ID',
    PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    INDEX idx_user_roles_user_id (user_id),
    INDEX idx_user_roles_role_id (role_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- ============================================
-- 3. 初始化默认角色
-- ============================================
INSERT IGNORE INTO roles (name, code, description) VALUES
('开发人员', 'developer', '负责开发任务的技术人员'),
('项目经理', 'project_manager', '负责项目管理和任务分配'),
('开发组长', 'development_lead', '负责团队管理和资源分配'),
('系统管理员', 'system_admin', '系统管理员，拥有所有权限');

-- ============================================
-- 4. 迁移现有用户的角色数据
-- ============================================
-- 将users表中的role字段迁移到user_roles关联表
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
INNER JOIN roles r ON u.role = r.code
WHERE u.role IS NOT NULL AND u.role != ''
ON DUPLICATE KEY UPDATE user_id = user_id;

-- ============================================
-- 5. 注意事项
-- ============================================
-- 1. role字段保留用于向后兼容，但不再使用
-- 2. 新系统应使用roles关系来管理用户角色
-- 3. 一个用户可以拥有多个角色
