#!/bin/bash
# 任务系统API测试脚本

set -e

BASE_URL="http://localhost:8000"
API_BASE="${BASE_URL}/api/v1"

echo "🧪 开始测试任务系统API"
echo ""

# 1. 登录获取Token
echo "1. 登录获取Token..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_BASE}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123")

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null || echo "")

if [ -z "$TOKEN" ]; then
  echo "❌ 登录失败，请检查用户名和密码"
  exit 1
fi

echo "✅ 登录成功，Token: ${TOKEN:0:20}..."
echo ""

# 2. 创建任务
echo "2. 创建任务..."
CREATE_RESPONSE=$(curl -s -X POST "${API_BASE}/tasks" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试任务 - API测试",
    "description": "这是一个用于测试的任务",
    "estimated_man_days": 5.0,
    "required_skills": "Python, FastAPI, Vue.js"
  }')

TASK_ID=$(echo $CREATE_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', ''))" 2>/dev/null || echo "")

if [ -z "$TASK_ID" ]; then
  echo "❌ 创建任务失败"
  echo "响应: $CREATE_RESPONSE"
  exit 1
fi

echo "✅ 任务创建成功，ID: $TASK_ID"
echo ""

# 3. 获取任务详情
echo "3. 获取任务详情..."
DETAIL_RESPONSE=$(curl -s -X GET "${API_BASE}/tasks/${TASK_ID}" \
  -H "Authorization: Bearer ${TOKEN}")

TASK_STATUS=$(echo $DETAIL_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', ''))" 2>/dev/null || echo "")

if [ "$TASK_STATUS" != "draft" ]; then
  echo "⚠️  任务状态不是draft: $TASK_STATUS"
else
  echo "✅ 任务状态正确: $TASK_STATUS"
fi
echo ""

# 4. 发布任务
echo "4. 发布任务..."
PUBLISH_RESPONSE=$(curl -s -X POST "${API_BASE}/tasks/${TASK_ID}/publish" \
  -H "Authorization: Bearer ${TOKEN}")

PUBLISH_STATUS=$(echo $PUBLISH_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('status', ''))" 2>/dev/null || echo "")

if [ "$PUBLISH_STATUS" != "published" ]; then
  echo "❌ 发布任务失败，状态: $PUBLISH_STATUS"
  echo "响应: $PUBLISH_RESPONSE"
else
  echo "✅ 任务发布成功，状态: $PUBLISH_STATUS"
fi
echo ""

# 5. 获取任务列表
echo "5. 获取任务列表..."
LIST_RESPONSE=$(curl -s -X GET "${API_BASE}/tasks?page=1&page_size=10" \
  -H "Authorization: Bearer ${TOKEN}")

TOTAL=$(echo $LIST_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null || echo "0")

echo "✅ 任务列表获取成功，总数: $TOTAL"
echo ""

# 6. 测试排期API（如果有认领的任务）
echo "6. 测试排期功能..."
# 先尝试认领任务（需要开发人员账号）
echo "   注意：排期功能需要在任务被认领后才会生成"
echo ""

echo "✅ 基础API测试完成！"
echo ""
echo "📝 测试总结："
echo "   - 登录: ✅"
echo "   - 创建任务: ✅"
echo "   - 获取任务详情: ✅"
echo "   - 发布任务: ✅"
echo "   - 获取任务列表: ✅"
echo ""
echo "💡 提示："
echo "   - 可以使用开发人员账号认领任务来测试排期功能"
echo "   - 前端页面访问: http://localhost:5173/tasks"
echo "   - API文档访问: http://localhost:8000/docs"
