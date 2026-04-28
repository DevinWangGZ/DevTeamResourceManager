-- MySQL/MariaDB: 协办项目经理（可多选）
CREATE TABLE IF NOT EXISTS `project_managers` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `project_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_project_managers_proj_user` (`project_id`,`user_id`),
    KEY `ix_project_managers_project_id` (`project_id`),
    KEY `ix_project_managers_user_id` (`user_id`),
    CONSTRAINT `fk_project_managers_project` FOREIGN KEY (`project_id`) REFERENCES `projects` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_project_managers_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
