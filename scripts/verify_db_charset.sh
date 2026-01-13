#!/bin/bash
# 验证数据库字符集和数据

MYSQL_HOST="${MYSQL_HOST:-10.254.68.77}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"
MYSQL_DB="${MYSQL_DB:-devteam_manager}"

echo "🔍 验证数据库字符集和数据..."
echo ""

# 检查数据库字符集
echo "1. 数据库字符集："
mysql -h "${MYSQL_HOST}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    --default-character-set=utf8mb4 \
    -e "SHOW CREATE DATABASE ${MYSQL_DB}\G" 2>/dev/null | grep -i "character\|collate" || true

echo ""
echo "2. 表字符集（users表）："
mysql -h "${MYSQL_HOST}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    --default-character-set=utf8mb4 \
    "${MYSQL_DB}" \
    -e "SHOW CREATE TABLE users\G" 2>/dev/null | grep -i "charset\|collate" | head -1 || true

echo ""
echo "3. 数据统计："
mysql -h "${MYSQL_HOST}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    --default-character-set=utf8mb4 \
    "${MYSQL_DB}" \
    -e "
    SELECT 
        (SELECT COUNT(*) FROM users) as users,
        (SELECT COUNT(*) FROM tasks) as tasks,
        (SELECT COUNT(*) FROM projects) as projects,
        (SELECT COUNT(*) FROM skills) as skills;
    " 2>/dev/null || true

echo ""
echo "4. 用户数据示例（前3条）："
mysql -h "${MYSQL_HOST}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    --default-character-set=utf8mb4 \
    "${MYSQL_DB}" \
    -e "SELECT id, username, email, role FROM users LIMIT 3;" 2>/dev/null || true

echo ""
echo "✅ 验证完成！"
echo ""
echo "💡 提示："
echo "   - 如果终端显示乱码，可能是终端编码问题"
echo "   - 可以通过应用访问数据验证是否正确"
echo "   - 或使用MySQL客户端工具（如Navicat）查看"
