-- 添加文章附件表
-- 版本: v1.1
-- 创建日期: 2025-01
-- 说明: 为知识分享功能添加附件支持（Word、PPT、PDF、Excel）

USE devteam_manager;

-- ============================================
-- 文章附件表 (article_attachments)
-- ============================================
CREATE TABLE IF NOT EXISTS article_attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    article_id INT NOT NULL COMMENT '文章ID',
    filename VARCHAR(255) NOT NULL COMMENT '原始文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径（相对路径）',
    file_size INT NOT NULL COMMENT '文件大小（字节）',
    file_type VARCHAR(50) NOT NULL COMMENT '文件类型: word, ppt, pdf, excel',
    mime_type VARCHAR(100) NOT NULL COMMENT 'MIME类型',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_article_attachments_article_id (article_id),
    CONSTRAINT fk_article_attachments_article FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文章附件表';
