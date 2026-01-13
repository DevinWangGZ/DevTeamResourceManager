-- DevTeam Manager 字符集设置脚本
-- 版本: v1.0
-- 创建日期: 2024-05
-- 用途: 在执行建表语句前设置正确的字符集

-- 设置客户端连接字符集为UTF-8
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET character_set_connection=utf8mb4;

-- 设置服务器端字符集
SET character_set_server=utf8mb4;
SET collation_server=utf8mb4_unicode_ci;

-- 显示当前字符集设置（用于验证）
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';
