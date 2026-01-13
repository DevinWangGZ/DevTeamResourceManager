#!/bin/bash
# MySQL数据库初始化脚本
# 自动设置字符集并执行SQL脚本

set -e

MYSQL_HOST="${MYSQL_HOST:-10.254.68.77}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-123456}"
MYSQL_DB="${MYSQL_DB:-devteam_manager}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_DIR="${SCRIPT_DIR}/backend/sql"

echo "🚀 开始初始化MySQL数据库..."
echo "数据库: ${MYSQL_DB}"
echo "主机: ${MYSQL_HOST}"
echo ""

# 检查SQL文件是否存在
if [ ! -f "${SQL_DIR}/01_create_tables_mysql.sql" ]; then
    echo "❌ 错误: 找不到建表SQL文件"
    exit 1
fi

if [ ! -f "${SQL_DIR}/02_init_data_mysql.sql" ]; then
    echo "❌ 错误: 找不到初始化数据SQL文件"
    exit 1
fi

# 执行建表语句
echo "📝 执行建表语句..."
mysql -h "${MYSQL_HOST}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    --default-character-set=utf8mb4 \
    < "${SQL_DIR}/01_create_tables_mysql.sql"

if [ $? -eq 0 ]; then
    echo "✅ 建表语句执行成功"
else
    echo "❌ 建表语句执行失败"
    exit 1
fi

# 执行初始化数据
echo ""
echo "📝 执行初始化数据..."
mysql -h "${MYSQL_HOST}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    --default-character-set=utf8mb4 \
    "${MYSQL_DB}" \
    < "${SQL_DIR}/02_init_data_mysql.sql"

if [ $? -eq 0 ]; then
    echo "✅ 初始化数据执行成功"
else
    echo "❌ 初始化数据执行失败"
    exit 1
fi

# 验证字符集
echo ""
echo "🔍 验证数据库字符集..."
mysql -h "${MYSQL_HOST}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}" \
    --default-character-set=utf8mb4 \
    "${MYSQL_DB}" \
    -e "SHOW CREATE DATABASE ${MYSQL_DB}\G" | grep -i "character\|collate" || true

echo ""
echo "✅ 数据库初始化完成！"
echo ""
echo "💡 提示："
echo "   - 如果发现乱码，请检查MySQL客户端字符集设置"
echo "   - 建议使用: mysql --default-character-set=utf8mb4"
echo "   - 或执行: SET NAMES utf8mb4;"
